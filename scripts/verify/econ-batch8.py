# Run after `npm run build`: python3 scripts/verify/econ-batch8.py
# Independent check of the economy pages for Tanzania, Uganda, DR Congo, Algeria and Iraq (task 130):
# reads the ORIGINAL World Bank zips (data/raw/wdi/), never the site's generated data, and
# confirms every figure in the text, Key facts, tables and CSVs, plus the claims behind each sentence.
import csv, io, zipfile, gzip, re, html, sys, json

def wdi(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        n = z.namelist()
        lines = z.read([x for x in n if x.startswith('API_')][0]).decode('utf-8-sig').splitlines()
        meta = list(csv.DictReader(io.StringIO(z.read([x for x in n if x.startswith('Metadata_Country')][0]).decode('utf-8-sig'))))
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    return ({r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)} for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))},
            {m['Country Code']: m for m in meta if m['Region']})

G, econ = wdi('NY.GDP.MKTP.CD'); PC, _ = wdi('NY.GDP.PCAP.CD'); PPP, _ = wdi('NY.GDP.PCAP.PP.CD'); GR, _ = wdi('NY.GDP.MKTP.KD.ZG')
INF, _ = wdi('FP.CPI.TOTL.ZG'); UN, _ = wdi('SL.UEM.TOTL.ZS'); REM, _ = wdi('BX.TRF.PWKR.CD.DT'); REMP, _ = wdi('BX.TRF.PWKR.DT.GD.ZS'); NET, _ = wdi('IT.NET.USER.ZS')
pop = {}
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz', 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Variant'] == 'Medium' and r['Time'] == '2025' and (r['ISO3_code'] in ('USA',) or r['Location'] == 'World'):
            pop[r['ISO3_code'] or 'WORLD'] = float(r['TPopulation1July'])

usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion" if v >= 1e9 else f"${v/1e6:.1f} million"
whole = lambda v: f"${round(v):,}"
intd = lambda v: f"Int${round(v):,}"
p1 = lambda v: f"{v:.1f}%"
sp = lambda v: ('+' if round(v, 1) > 0 else '') + f"{v:.1f}%"
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"
L = 2025
rank = lambda src, c, y=L: [k for k, _ in sorted([(k, s[y]) for k, s in src.items() if k in econ and y in s], key=lambda x: -x[1])].index(c) + 1
last = lambda src, c: (max(src[c]), src[c][max(src[c])])
ok = 0; bad = []

def page(slug):
    p = open(f'dist/country/{slug}/economy/index.html').read()
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', p, flags=re.S))))
    return p, t
def expect(t, slug, d):
    global ok
    for k, v in d.items():
        if v in t: ok += 1
        else: bad.append(f'{slug}: {k} {v} not on the page')
def claim(slug, k, c):
    global ok
    if c: ok += 1
    else: bad.append(f'{slug}: claim false: {k}')
def common(slug, c, years):
    """Figures every page shows (Key facts, cards, table, CSV)."""
    global ok
    p, t = page(slug)
    iy, iv = last(INF, c)
    d = {'GDP': usd(G[c][L]), 'GDP per person': whole(PC[c][L]), 'growth': sp(GR[c][L]), 'inflation': p1(iv), 'share of world': p1(G[c][L] / G['WLD'][L] * 100),
         'GDP rank': ordn(rank(G, c)), 'PPP': intd(PPP[c][L]), 'unemployment': p1(UN[c][L]), 'internet': p1(last(NET, c)[1]), **({'remittances': usd(last(REM, c)[1])} if REM.get(c) else {})}
    expect(t, slug, d)
    for tr in re.findall(r'<tr[^>]*data-year="(\d{4})"[^>]*>(.*?)</tr>', p, re.S):
        y = int(tr[0]); cells = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', tr[1], re.S)]
        want = [f"{G[c][y]/1e9:.1f}" if y in G[c] else '–', whole(PC[c][y]) if y in PC[c] else '–', sp(GR[c][y]) if y in GR[c] else '–', p1(INF[c][y]) if y in INF[c] else '–', p1(REMP[c][y]) if y in REMP[c] else '–']
        if cells == want: ok += 1
        else: bad.append(f'{slug} table {y}: {cells} ≠ {want}')
    rows = [l for l in open(f'dist/data/{slug}-economy.csv').read().splitlines() if l and not l.startswith('#')][1:]
    for l in rows:
        f = l.split(','); y = int(f[0])
        for i, src in enumerate([G, PC, PPP, GR, INF, UN, REM, REMP, NET]):
            w = src[c].get(y)
            if (w is None and f[i + 1] == '') or (w is not None and float(f[i + 1]) == w): ok += 1
            else: bad.append(f'{slug} CSV {y} col {i+1}')
    return t

neg = lambda c: [y for y in sorted(GR[c]) if GR[c][y] < 0]
below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]
AFR = lambda k: econ[k]['Region'] == 'Sub-Saharan Africa' or k in ('DZA', 'EGY', 'LBY', 'MAR', 'TUN')
LAC = lambda k: econ[k]['Region'] == 'Latin America & Caribbean'
peak = lambda S, c: max(S[c], key=S[c].get)


# ---------- Tanzania ----------
s, c = 'tanzania', 'TZA'; t = common(s, c, None)
af = order(G, L, AFR); ua = order(UN, L)[::-1]
expect(t, s, {'COD': usd(G['COD'][L]), 'g2021': p1(GR[c][2021]), 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'gdp2000': usd(G[c][2000]),
              'mult': f"{G[c][L] / G[c][2000]:.1f}", 'u rank': ordn(ua.index(c) + 1), 'infl max': p1(INF[c][1984])})
claim(s, 'record GDP and per person; 82nd; 12th in Africa between COD and UGA', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 82 and af[10:13] == ['COD', c, 'UGA'])
claim(s, 'growth up each year since 2021; best since 2017; none negative since 1984', all(GR[c][y] > GR[c][y - 1] for y in range(2022, L + 1)) and above_since(GR, c, L) == 2017 and neg(c)[-1] == 1983)
claim(s, 'unemployment 12th lowest; inflation <5% since 2018, peak 1984', ua.index(c) == 11 and all(INF[c][y] < 5 for y in range(2018, L + 1)) and peak(INF, c) == 1984)
claim(s, 'nearly doubled since 2015; smaller than Kenya; remittances 2024', 1.8 < G[c][L] / G[c][2015] < 2.05 and G[c][L] < G['KEN'][L] and max(REM[c]) == 2024)

# ---------- Uganda ----------
s, c = 'uganda', 'UGA'; t = common(s, c, None)
ssa = order(REM, L, lambda k: econ[k]['Region'] == 'Sub-Saharan Africa'); ny = max(NET[c]); netlow = order(NET, ny)[::-1]
expect(t, s, {'g2020': p1(GR[c][2020]), 'infl2022': p1(INF[c][2022]), 'times': f"{REM[c][L] / REM[c][2015]:.1f} times", 'rem %': p1(REMP[c][L]), 'rank': ordn(rank(G, c))})
claim(s, 'record GDP and per person; low income', peak(G, c) == L and peak(PC, c) == L and econ[c]['IncomeGroup'] == 'Low income')
claim(s, 'declines only 1984-85, series from 1983; best since 2019', neg(c) == [1984, 1985] and min(GR[c]) == 1983 and above_since(GR, c, L) == 2019)
claim(s, 'internet second-lowest in 2024 after Burundi', ny == 2024 and netlow[:2] == ['BDI', c])
claim(s, 'record remittances, >3x 2015, 4th in SSA', peak(REM, c) == L and REM[c][L] > 3 * REM[c][2015] and ssa[:4] == ['NGA', 'KEN', 'COD', c])
claim(s, 'inflation peak 2011', peak(INF, c) == 2011)

# ---------- DR Congo ----------
s, c = 'dr-congo', 'COD'; t = common(s, c, None)
expect(t, s, {'g1993': p1(abs(GR[c][1993])), 'infl2016': p1(INF[c][2016]), 'pc': whole(PC[c][L]), 'net': p1(NET[c][max(NET[c])])})
claim(s, 'record GDP; 11th in Africa', peak(G, c) == L and order(G, L, AFR).index(c) == 10)
claim(s, 'falls every year 1989-2001 except 1995', all(GR[c][y] < 0 for y in range(1989, 2002) if y != 1995) and GR[c][1995] > 0)
claim(s, '1993 deepest of the 1989-2001 run', min(range(1989, 2002), key=lambda y: GR[c][y]) == 1993)
claim(s, '8th-lowest per person; growth >5% since 2022', order(PC, L)[::-1].index(c) == 7 and all(GR[c][y] > 5 for y in range(2022, L + 1)))
claim(s, 'CPI ends 2016; >1000% 1991-94; 1994 peak', max(INF[c]) == 2016 and [y for y in INF[c] if INF[c][y] > 1000] == [1991, 1992, 1993, 1994] and peak(INF, c) == 1994 and 23000 < INF[c][1994] < 24000)
claim(s, 'record remittances, third in SSA', peak(REM, c) == L and order(REM, L, lambda k: econ[k]['Region'] == 'Sub-Saharan Africa')[:3] == ['NGA', 'KEN', c])

# ---------- Algeria ----------
s, c = 'algeria', 'DZA'; t = common(s, c, None)
expect(t, s, {'infl2022': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]), 'pc2014': whole(PC[c][2014]), 'pc2020': whole(PC[c][2020]), 'u1995': p1(UN[c][1995]), 'u2013': p1(UN[c][2013]), 'g2020': p1(abs(GR[c][2020]))})
claim(s, 'record GDP; 4th in Africa; 50th', peak(G, c) == L and order(G, L, AFR)[:4] == ['ZAF', 'EGY', 'NGA', c] and rank(G, c) == 50)
claim(s, 'per person just below 2014 peak', peak(PC, c) == 2014 and 0.99 * PC[c][2014] < PC[c][L] < PC[c][2014])
claim(s, 'inflation lowest since 2005; unemployment lowest since 2016, peak 1995, low 2013', below_since(INF, c, L) == 2005 and below_since(UN, c, L) == 2016 and peak(UN, c) == 1995 and min(UN[c], key=UN[c].get) == 2013)
claim(s, 'growth >3% each year 2021-25 after 2020 fall', GR[c][2020] < 0 and all(GR[c][y] > 3 for y in range(2021, L + 1)))

# ---------- Iraq ----------
s, c = 'iraq', 'IRQ'; t = common(s, c, None)
expect(t, s, {'g2024': p1(abs(GR[c][2024])), 'g2022': p1(GR[c][2022]), 'peak': usd(G[c][2022]), 'g1991': p1(abs(GR[c][1991])), 'g2003': p1(abs(GR[c][2003])), 'g2020': p1(abs(GR[c][2020])),
              'u rank': ordn(order(UN, L).index(c) + 1), 'u2021': p1(UN[c][2021])})
claim(s, 'two declines; GDP peak 2022, lowest since 2021', GR[c][2024] < 0 and GR[c][L] < 0 and GR[c][2023] > 0 and peak(G, c) == 2022 and below_since(G, c, L) == 2021)
claim(s, '14th-highest unemployment; peak 2021; about one in seven', order(UN, L).index(c) == 13 and peak(UN, c) == 2021 and 13 < UN[c][L] < 16)
claim(s, 'inflation lowest since 2019; 1991 worst', below_since(INF, c, L) == 2019 and min(GR[c], key=GR[c].get) == 1991)
claim(s, 'remittances <1% of GDP; unemployment >15% since 2020', REMP[c][L] < 1 and all(UN[c][y] > 15 for y in range(2020, L + 1)))

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
