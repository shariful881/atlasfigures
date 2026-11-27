# Run after `npm run build`: python3 scripts/verify/econ-batch1.py
# Independent check of the economy pages for Italy, Spain, the Netherlands, Sweden and Switzerland (task 127):
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

below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]

G7 = ['USA', 'GBR', 'DEU', 'JPN', 'FRA', 'ITA', 'CAN']

# ---------- Italy ----------
s, c = 'italy', 'ITA'; t = common(s, c, None)
expect(t, s, {'RUS': usd(G['RUS'][L]), 'g2024': p1(GR[c][2024]), 'g2023': p1(GR[c][2023]), 'g2020': sp(GR[c][2020]), 'g2021': p1(GR[c][2021]), 'unemp 2014': p1(UN[c][2014]),
              'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'pc rank': ordn(rank(PC, c))})
claim(s, '9th, Russia 8th, gap < $20B', rank(G, c) == 9 and rank(G, 'RUS') == 8 and G['RUS'][L] - G[c][L] < 2e10)
claim(s, 'records GDP and per person', max(G[c], key=G[c].get) == L and max(PC[c], key=PC[c].get) == L)
claim(s, 'only Germany slower in G7', [k for k in G7 if k != c and GR[k][L] < GR[c][L]] == ['DEU'])
claim(s, '2012-14 declines; 2020 worst since 1961', all(GR[c][y] < 0 for y in (2012, 2013, 2014)) and min(GR[c], key=GR[c].get) == 2020 and min(GR[c]) == 1961)
claim(s, 'unemployment lowest since 2007, peak 2014', below_since(UN, c, L) == 2007 and max(UN[c], key=UN[c].get) == 2014)
claim(s, '2022 inflation highest since 1985', above_since(INF, c, 2022) == 1985)

# ---------- Spain ----------
s, c = 'spain', 'ESP'; t = common(s, c, None)
expect(t, s, {'DEU g': p1(GR['DEU'][L]), 'FRA g': p1(GR['FRA'][L]), 'ITA g': p1(GR['ITA'][L]), 'NLD g': p1(GR['NLD'][L]), 'g2024': p1(GR[c][2024]), 'unemp 2013': p1(UN[c][2013]),
              'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'g2022': p1(GR[c][2022]), 'infl 2022': p1(INF[c][2022]), 'pc rank': ordn(rank(PC, c))})
claim(s, '12th, record GDP', rank(G, c) == 12 and max(G[c], key=G[c].get) == L)
claim(s, 'faster than DEU FRA ITA NLD', all(GR[k][L] < GR[c][L] for k in ('DEU', 'FRA', 'ITA', 'NLD')))
claim(s, 'unemployment peak 2013, lowest since 2007, down since 2020, above 10%', max(UN[c], key=UN[c].get) == 2013 and below_since(UN, c, L) == 2007 and all(UN[c][y] < UN[c][y - 1] for y in range(2021, L + 1)) and UN[c][L] > 10)
claim(s, '2020 worst since 1961; 2022 inflation highest since 1986', min(GR[c], key=GR[c].get) == 2020 and min(GR[c]) == 1961 and above_since(INF, c, 2022) == 1986)

# ---------- Netherlands ----------
s, c = 'netherlands', 'NLD'; t = common(s, c, None)
ny = max(NET[c])
netr = [k for k, _ in sorted([(k, v[ny]) for k, v in NET.items() if k in econ and ny in v], key=lambda x: -x[1])].index(c) + 1
expect(t, s, {'g2023': p1(abs(GR[c][2023])), 'g2024': p1(GR[c][2024]), 'infl 2022': p1(INF[c][2022]), 'infl 2024': p1(INF[c][2024]), 'unemp 2023': p1(UN[c][2023]), 'unemp 2024': p1(UN[c][2024]),
              'net rank': ordn(netr)})
claim(s, '18th GDP, 10th per person, record GDP', rank(G, c) == 18 and rank(PC, c) == 10 and max(G[c], key=G[c].get) == L)
claim(s, '2022 inflation highest since 1975; latest lowest since 2021, above 3%', above_since(INF, c, 2022) == 1975 and below_since(INF, c, L) == 2021 and INF[c][L] > 3)
claim(s, '2023 decline; growth best since 2022', GR[c][2023] < 0 and above_since(GR, c, L) == 2022)
claim(s, 'unemployment rising two years, under 4%', UN[c][2023] < UN[c][2024] < UN[c][L] < 4)

# ---------- Sweden ----------
s, c = 'sweden', 'SWE'; t = common(s, c, None)
expect(t, s, {'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'unemp 2023': p1(UN[c][2023]), 'unemp 2024': p1(UN[c][2024]), 'unemp 1997': p1(UN[c][1997]),
              'g2023': p1(abs(GR[c][2023])), 'g2024': p1(GR[c][2024]), 'g2009': sp(GR[c][2009]), 'pc rank': ordn(rank(PC, c))})
claim(s, '25th, 13th per person', rank(G, c) == 25 and rank(PC, c) == 13)
claim(s, '2022 and 2023 highest since 1991; latest lowest since 2020', above_since(INF, c, 2023) == 1991 and above_since(INF, c, 2022) == 1991 and below_since(INF, c, L) == 2020)
claim(s, 'unemployment highest since 2021, peak 1997', above_since(UN, c, L) == 2021 and max(UN[c], key=UN[c].get) == 1997)
claim(s, '2009 worst; 1991-93 declines', min(GR[c], key=GR[c].get) == 2009 and all(GR[c][y] < 0 for y in (1991, 1992, 1993)))

# ---------- Switzerland ----------
s, c = 'switzerland', 'CHE'; t = common(s, c, None)
pcr = order(PC, L)
eca = [k for k, _ in sorted([(k, v[L]) for k, v in INF.items() if k in econ and L in v and econ[k]['Region'] == 'Europe & Central Asia'], key=lambda x: x[1])]
expect(t, s, {'LUX': whole(PC['LUX'][L]), 'IRL': whole(PC['IRL'][L]), 'g2024': p1(GR[c][2024]), 'infl 2022': p1(INF[c][2022]), 'unemp 2024': p1(UN[c][2024]), 'unemp 1991': p1(UN[c][1991])})
claim(s, '3rd per person after LUX, IRL', pcr[:3] == ['LUX', 'IRL', c])
claim(s, 'first year above $1T; 20th', all(G[c][y] < 1e12 for y in G[c] if y != L) and G[c][L] >= 1e12 and rank(G, c) == 20)
claim(s, 'second-lowest inflation in ECA after Cyprus', eca[:2] == ['CYP', c])
claim(s, 'prices fell 2012-16 and 2020', [y for y in INF[c] if y >= 2010 and INF[c][y] < 0] == [2012, 2013, 2014, 2015, 2016, 2020])
claim(s, '2022 highest since 1993; unemployment highest since 2021', above_since(INF, c, 2022) == 1993 and above_since(UN, c, L) == 2021)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
