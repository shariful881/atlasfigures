# Run after `npm run build`: python3 scripts/verify/econ-batch9.py
# Independent check of the economy pages for Iran, Myanmar, Nepal, Sri Lanka and Afghanistan (task 131):
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


def common_at(slug, c, Lc):
    """Like common(), for a page whose latest GDP year is Lc (UAE)."""
    global ok
    p, t = page(slug)
    d = {'GDP': usd(G[c][Lc]), 'GDP per person': whole(PC[c][Lc]), 'growth': sp(GR[c][Lc]), 'PPP': intd(PPP[c][Lc]), 'inflation': p1(last(INF, c)[1]), 'internet': p1(last(NET, c)[1])}
    expect(t, slug, d)
    rows = [l for l in open(f'dist/data/{slug}-economy.csv').read().splitlines() if l and not l.startswith('#')][1:]
    for l in rows:
        f = l.split(','); y = int(f[0])
        for i, src in enumerate([G, PC, PPP, GR, INF, UN, REM, REMP, NET]):
            w = src.get(c, {}).get(y)
            if (w is None and f[i + 1] == '') or (w is not None and float(f[i + 1]) == w): ok += 1
            else: bad.append(f'{slug} CSV {y} col {i+1}')
    return t


# ---------- Iran ----------
s, c = 'iran', 'IRN'; t = common(s, c, None)
expect(t, s, {'TUR': p1(INF['TUR'][L]), 'infl max': p1(INF[c][1995]), 'peak': usd(G[c][2012]), 'pc peak': whole(PC[c][2012]), 'u2010': p1(UN[c][2010]), 'rank': ordn(rank(G, c))})
claim(s, 'highest inflation 2025, TUR second; >30% since 2019; record 1995', order(INF, L)[:2] == [c, 'TUR'] and all(INF[c][y] > 30 for y in range(2019, L + 1)) and peak(INF, c) == 1995)
claim(s, 'first decline since 2019', GR[c][L] < 0 and neg(c)[-2] == 2019 and all(GR[c][y] > 0 for y in range(2020, L)))
claim(s, 'GDP and per person peak 2012; GDP <60% of peak, lowest since 2020; per person roughly halved', peak(G, c) == 2012 and peak(PC, c) == 2012 and G[c][L] < 0.6 * G[c][2012] and below_since(G, c, L) == 2020 and 0.45 < PC[c][L] / PC[c][2012] < 0.5)
claim(s, 'unemployment peak 2010; remittances end 2004', peak(UN, c) == 2010 and max(REM[c]) == 2004)

# ---------- Myanmar ----------
s, c = 'myanmar', 'MMR'; t = common(s, c, None)
expect(t, s, {'g2024': p1(abs(GR[c][2024])), 'g2021': p1(abs(GR[c][2021])), 'g2020': p1(abs(GR[c][2020])), 'infl2019': p1(INF[c][2019]), 'rem2019': usd(REM[c][2019]), 'net2020': p1(NET[c][2020])})
claim(s, '2021 worst; falls 2020, 2021, 2024, 2025', min(GR[c], key=GR[c].get) == 2021 and [y for y in range(2020, L + 1) if GR[c][y] < 0] == [2020, 2021, 2024, L])
claim(s, 'record dollar GDP; per person just under 2020', peak(G, c) == L and peak(PC, c) == 2020 and PC[c][L] > 0.99 * PC[c][2020])
claim(s, 'CPI and remittances end 2019; internet 2020; CPI peak 2002; 84th', max(INF[c]) == 2019 and max(REM[c]) == 2019 and max(NET[c]) == 2020 and peak(INF, c) == 2002 and rank(G, c) == 84)

# ---------- Nepal ----------
s, c = 'nepal', 'NPL'; t = common(s, c, None)
expect(t, s, {'rem %': p1(REMP[c][L]), 'rem rank': ordn(rank(REM, c)), 'times': f"{REM[c][L] / REM[c][2015]:.1f}", 'g2020': p1(abs(GR[c][2020])), 'infl2022': p1(INF[c][2022])})
claim(s, 'remittance share 3rd after TJK, TON; record; >30%', order(REMP, L)[:3] == ['TJK', 'TON', c] and peak(REMP, c) == L and REMP[c][L] > 30)
claim(s, 'record remittances, 15th, >2x 2015; record GDP and per person', peak(REM, c) == L and rank(REM, c) == 15 and REM[c][L] > 2 * REM[c][2015] and peak(G, c) == L and peak(PC, c) == L)
claim(s, 'inflation lowest since 2007; 2020 only decline since 1983', below_since(INF, c, L) == 2007 and neg(c)[-2:] == [1983, 2020])

# ---------- Sri Lanka ----------
s, c = 'sri-lanka', 'LKA'; t = common(s, c, None)
expect(t, s, {'infl2024': p1(abs(INF[c][2024])), 'infl max': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]), 'g2022': p1(abs(GR[c][2022])), 'g2023': p1(abs(GR[c][2023])), 'g2024': p1(GR[c][2024]), 'rem %': p1(REMP[c][L]), 'rem rank': ordn(rank(REM, c))})
claim(s, 'lowest inflation in the world; deflation 2024-25; earlier only 1960, 1966; peak 2022', order(INF, L)[-1] == c and [y for y in INF[c] if INF[c][y] < 0] == [1960, 1966, 2024, L] and peak(INF, c) == 2022)
claim(s, 'declines 2019, 2020, 2022, 2023; ~5% growth 2024-25; record GDP, per person; 71st', all(GR[c][y] < 0 for y in (2019, 2020, 2022, 2023)) and GR[c][2024] > 4.9 and GR[c][L] > 4.9 and peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 71)
claim(s, 'record remittances, 29th', peak(REM, c) == L and rank(REM, c) == 29)

# ---------- Afghanistan ----------
s, c, Lc = 'afghanistan', 'AFG', 2024
t = common_at(s, c, Lc)
expect(t, s, {'g2021': p1(abs(GR[c][2021])), 'g2022': p1(abs(GR[c][2022])), 'g2023': p1(GR[c][2023]), 'peak': usd(G[c][2014]), 'infl2023': p1(abs(INF[c][2023])), 'u24': p1(UN[c][2024]), 'u25': p1(UN[c][L]), 'u2022': p1(UN[c][2022])})
claim(s, 'latest GDP 2024; series from 2000; below 2014 peak; 2021 worst', max(G[c]) == Lc and min(G[c]) == 2000 and peak(G, c) == 2014 and min(GR[c], key=GR[c].get) == 2021)
claim(s, 'second-lowest per person in 2024 after Burundi', order(PC, Lc)[::-1][:2] == ['BDI', c])
claim(s, 'deflation 2023-24; earlier 2009, 2015', [y for y in INF[c] if INF[c][y] < 0] == [2009, 2015, 2023, 2024])
claim(s, 'unemployment peak 2022; remittances end 2020; internet from 1990', peak(UN, c) == 2022 and max(REM[c]) == 2020 and min(NET[c]) == 1990)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
