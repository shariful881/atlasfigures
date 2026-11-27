# Run after `npm run build`: python3 scripts/verify/econ-batch1.py
# Independent check of the economy pages for Mexico, the Philippines, Egypt, Vietnam and Turkey (task 109):
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
         'GDP rank': ordn(rank(G, c)), 'PPP': intd(PPP[c][L]), 'unemployment': p1(UN[c][L]), 'internet': p1(last(NET, c)[1]), 'remittances': usd(last(REM, c)[1])}
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

g7 = ['USA', 'GBR', 'DEU', 'JPN', 'FRA', 'ITA', 'CAN']
neg = lambda c: [y for y in sorted(GR[c]) if GR[c][y] < 0]
highest_since = lambda src, c, y: max(k for k in src[c] if k < y and src[c][k] > src[c][y])

below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]

# ---------- Mexico ----------
s, c = 'mexico', 'MEX'; t = common(s, c, None)
lac = order(G, L, lambda k: econ[k]['Region'] == 'Latin America & Caribbean')
expect(t, s, {'BRA': usd(G['BRA'][L]), 'rem 2024': usd(REM[c][2024]), 'rem 2015': usd(REM[c][2015]), 'g2021': p1(GR[c][2021]), 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]),
              'g2024': p1(GR[c][2024]), 'g2020': p1(abs(GR[c][2020])), 'g1995': sp(GR[c][1995]), 'g2009': sp(GR[c][2009]), 'infl 2022': p1(INF[c][2022]), 'pc rank': ordn(rank(PC, c))})
claim(s, '14th, second in LAC', rank(G, c) == 14 and lac[:2] == ['BRA', c])
claim(s, 'GDP record', max(G[c], key=G[c].get) == L)
claim(s, 'remittances 2nd after India, below 2024 record, >2x 2015', order(REM, L)[:2] == ['IND', c] and max(REM[c], key=REM[c].get) == 2024 and REM[c][L] > 2 * REM[c][2015])
claim(s, 'growth slower every year 2021-2025, weakest since 2020', all(GR[c][y] < GR[c][y - 1] for y in range(2022, L + 1)) and below_since(GR, c, L) == 2020)
claim(s, '2020 worst since 1961', min(GR[c], key=GR[c].get) == 2020 and min(GR[c]) == 1961)
claim(s, 'unemployment lowest since 2001; inflation lowest since 2020, about half 2022', below_since(UN, c, L) == 2001 and below_since(INF, c, L) == 2020 and 0.45 < INF[c][L] / INF[c][2022] < 0.55)

# ---------- Philippines ----------
s, c = 'philippines', 'PHL'; t = common(s, c, None)
expect(t, s, {'g2024': p1(GR[c][2024]), 'g2022': p1(GR[c][2022]), 'g2021': p1(GR[c][2021]), 'g2020': p1(abs(GR[c][2020])), 'infl 2023': p1(INF[c][2023]), 'rem %': p1(REMP[c][L]), 'pc rank': ordn(rank(PC, c))})
claim(s, '32nd, GDP record', rank(G, c) == 32 and max(G[c], key=G[c].get) == L)
claim(s, 'remittances 4th after IND MEX FRA, record, up since 2021', order(REM, L)[:4] == ['IND', 'MEX', 'FRA', c] and max(REM[c], key=REM[c].get) == L and all(REM[c][y] > REM[c][y - 1] for y in range(2022, L + 1)))
claim(s, 'growth slowest since 2020; 2020 worst since 1961', below_since(GR, c, L) == 2020 and min(GR[c], key=GR[c].get) == 2020 and min(GR[c]) == 1961)
claim(s, 'inflation lowest since 2016', below_since(INF, c, L) == 2016)
claim(s, 'unemployment level with the series low since 1991', UN[c][L] - min(UN[c].values()) < 0.05 and min(UN[c]) == 1991)

# ---------- Egypt ----------
s, c = 'egypt', 'EGY'; t = common(s, c, None)
NA = ['DZA', 'EGY', 'LBY', 'MAR', 'TUN']
afr = order(G, L, lambda k: econ[k]['Region'] == 'Sub-Saharan Africa' or k in NA)
pk = max(G[c], key=G[c].get)
expect(t, s, {'ZAF': usd(G['ZAF'][L]), 'NGA': usd(G['NGA'][L]), 'peak': usd(G[c][pk]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'g1968': sp(GR[c][1968]),
              'infl 2023': p1(INF[c][2023]), 'infl 2024': p1(INF[c][2024]), 'rem 2023': usd(REM[c][2023]), 'rem %': p1(REMP[c][L]), 'rem rank': f"{ordn(rank(REM, c))} largest"})
claim(s, 'second in Africa', afr[:3] == ['ZAF', c, 'NGA'])
claim(s, 'dollar GDP peak 2022, lower each year since; real growth positive', pk == 2022 and all(G[c][y] < G[c][y - 1] for y in (2023, 2024, L)) and all(GR[c][y] > 0 for y in (2023, 2024, L)))
claim(s, 'only decline since 1961 in 1968', neg(c) == [1968] and min(GR[c]) == 1961)
claim(s, '2023 inflation series high from 1960; latest lowest since 2022', max(INF[c], key=INF[c].get) == 2023 and min(INF[c]) == 1960 and below_since(INF, c, L) == 2022)
claim(s, 'remittances 5th, record, >2x 2023', rank(REM, c) == 5 and max(REM[c], key=REM[c].get) == L and REM[c][L] > 2 * REM[c][2023])

# ---------- Vietnam ----------
s, c = 'vietnam', 'VNM'; t = common(s, c, None)
expect(t, s, {'IDN pc': whole(PC['IDN'][L]), 'g2024': p1(GR[c][2024]), 'g2022': p1(GR[c][2022]), 'g2020': p1(GR[c][2020]), 'g2021': p1(GR[c][2021]), 'infl peak': p1(INF[c][2008]),
              'rem 2004': usd(REM[c][2004]), 'net': p1(NET[c][2024])})
claim(s, '31st, record GDP', rank(G, c) == 31 and max(G[c], key=G[c].get) == L)
claim(s, 'no decline since 1985', min(GR[c]) == 1985 and not neg(c))
claim(s, 'growth highest since 2022', above_since(GR, c, L) == 2022)
claim(s, 'per person ahead of Indonesia only in 1987 and 2025', [y for y in PC[c] if y in PC['IDN'] and PC[c][y] > PC['IDN'][y]] == [1987, L])
claim(s, 'passed $100B in 2009, about 5x since; Indonesia ~2.8x', min(y for y in G[c] if G[c][y] >= 1e11) == 2009 and 4.5 < G[c][L] / G[c][2009] < 5.5 and 2.6 < G['IDN'][L] / G[c][L] < 3)
claim(s, 'inflation peak 2008, series from 1996; remittances end 2004', max(INF[c], key=INF[c].get) == 2008 and min(INF[c]) == 1996 and max(REM[c]) == 2004)

# ---------- Turkey ----------
s, c = 'turkey', 'TUR'; t = common(s, c, None)
expect(t, s, {'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'infl 2024': p1(INF[c][2024]), 'infl 1994': p1(INF[c][1994]), 'g2024': p1(GR[c][2024]), 'g2021': p1(GR[c][2021]),
              'g2009': sp(GR[c][2009]), 'unemp 2009': p1(UN[c][2009])})
claim(s, '16th, records in GDP and per person', rank(G, c) == 16 and max(G[c], key=G[c].get) == L and max(PC[c], key=PC[c].get) == L)
claim(s, '2022 inflation highest since 1998; peak 1994; latest lowest since 2021', above_since(INF, c, 2022) == 1998 and max(INF[c], key=INF[c].get) == 1994 and below_since(INF, c, L) == 2021)
claim(s, 'no decline since 2009; 2021 best since 2010', [y for y in neg(c) if y >= 2009] == [2009] and max((y for y in GR[c] if y >= 2010), key=GR[c].get) == 2021)
claim(s, 'unemployment lowest since 2001, down 5 years, peak 2009', below_since(UN, c, L) == 2001 and all(UN[c][y] < UN[c][y - 1] for y in range(2021, L + 1)) and max(UN[c], key=UN[c].get) == 2009)
claim(s, 'upper middle income', econ[c]['IncomeGroup'] == 'Upper middle income')

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
