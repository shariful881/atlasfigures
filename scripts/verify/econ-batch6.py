# Run after `npm run build`: python3 scripts/verify/econ-batch1.py
# Independent check of the economy pages for Saudi Arabia, the UAE, Singapore, Malaysia and Thailand (task 128):
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

g7 = ['USA', 'GBR', 'DEU', 'JPN', 'FRA', 'ITA', 'CAN']
neg = lambda c: [y for y in sorted(GR[c]) if GR[c][y] < 0]
highest_since = lambda src, c, y: max(k for k in src[c] if k < y and src[c][k] > src[c][y])

below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]

below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]

below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]

below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]

SEA = ['BRN', 'IDN', 'KHM', 'LAO', 'MMR', 'MYS', 'PHL', 'SGP', 'THA', 'TLS', 'VNM']  # UN M49 South-eastern Asia

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

# ---------- Saudi Arabia ----------
s, c = 'saudi-arabia', 'SAU'; t = common(s, c, None)
mena = order(G, L, lambda k: econ[k]['Region'] == 'Middle East & North Africa')
pp = max(PC[c], key=PC[c].get)
expect(t, s, {'ARE 2024': usd(G['ARE'][2024]), 'g2024': p1(GR[c][2024]), 'g2023': p1(GR[c][2023]), 'g2022': p1(GR[c][2022]), 'g1982': p1(abs(GR[c][1982])), 'unemp 2020': p1(UN[c][2020]),
              'pc peak': whole(PC[c][pp]), 'pc rank': ordn(rank(PC, c))})
claim(s, '19th, largest in MENA; UAE no 2025 and smaller', rank(G, c) == 19 and mena[0] == c and L not in G['ARE'] and G['ARE'][2024] < G[c][L])
claim(s, 'record GDP; per person peak 2022', max(G[c], key=G[c].get) == L and pp == 2022)
claim(s, '2022 best since 1976; latest best since 2022', above_since(GR, c, 2022) == 1976 and above_since(GR, c, L) == 2022)
claim(s, 'unemployment record low since 1991, down 5 years', min(UN[c], key=UN[c].get) == L and min(UN[c]) == 1991 and all(UN[c][y] < UN[c][y - 1] for y in range(2021, L + 1)))
claim(s, '1982-85 declines, 1982 worst', all(GR[c][y] < 0 for y in (1982, 1983, 1984, 1985)) and min(GR[c], key=GR[c].get) == 1982)

# ---------- UAE ----------
s, c, Lc = 'united-arab-emirates', 'ARE', 2024
t = common_at(s, c, Lc)
r24 = order(G, Lc); p24 = order(PC, Lc); pp = max(PC[c], key=PC[c].get)
expect(t, s, {'rank': f"{ordn(r24.index(c) + 1)} among", 'pc peak': whole(PC[c][pp]), 'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]),
              'g1986': sp(GR[c][1986]), 'unemp': p1(UN[c][Lc])})
claim(s, 'latest GDP 2024, no 2025', max(G[c]) == Lc and L not in G[c])
claim(s, '27th by GDP and per person in 2024', r24.index(c) + 1 == 27 and p24.index(c) + 1 == 27)
claim(s, 'record GDP; per person peak 2013; 1986 worst', max(G[c], key=G[c].get) == Lc and pp == 2013 and min(GR[c], key=GR[c].get) == 1986)
claim(s, 'inflation 2025 lowest since 2021; no remittances', max(INF[c]) == L and below_since(INF, c, L) == 2021 and not REM.get(c))

# ---------- Singapore ----------
s, c = 'singapore', 'SGP'; t = common(s, c, None)
seaR = [k for k, _ in sorted([(k, G[k][L]) for k in SEA if L in G.get(k, {})], key=lambda x: -x[1])]
expect(t, s, {'g2024': p1(GR[c][2024]), 'g2023': p1(GR[c][2023]), 'g2020': sp(GR[c][2020]), 'gdp 2000': usd(G[c][2000]), 'times': f"about {int(G[c][L] / G[c][2000])} times", 'infl 2022': p1(INF[c][2022])})
claim(s, 'first at PPP, 4th in dollars after LUX IRL CHE', order(PPP, L)[0] == c and order(PC, L)[:4] == ['LUX', 'IRL', 'CHE', c])
claim(s, '27th, second in SE Asia', rank(G, c) == 27 and seaR[:2] == ['IDN', c])
claim(s, 'five declines since 1961', neg(c) == [1964, 1985, 1998, 2001, 2020] and min(GR[c]) == 1961)
claim(s, 'inflation lowest since 2020', below_since(INF, c, L) == 2020)

# ---------- Malaysia ----------
s, c = 'malaysia', 'MYS'; t = common(s, c, None)
ny = max(NET[c]); netr = order(NET, ny).index(c) + 1
expect(t, s, {'g2024': p1(GR[c][2024]), 'g2023': p1(GR[c][2023]), 'g2022': p1(GR[c][2022]), 'g1998': sp(GR[c][1998]), 'infl 2022': p1(INF[c][2022]), 'net rank': ordn(netr),
              'rem rank': ordn(rank(REM, c)), 'rem %': p1(REMP[c][L]), 'pc rank': ordn(rank(PC, c))})
claim(s, '33rd, record GDP, ~5x 2000', rank(G, c) == 33 and max(G[c], key=G[c].get) == L and 5 < G[c][L] / G[c][2000] < 5.1)
claim(s, 'growth best since 2022; inflation lowest since 2020', above_since(GR, c, L) == 2022 and below_since(INF, c, L) == 2020)
claim(s, 'declines 1985, 1998, 2009, 2020; 1998 worst', neg(c) == [1985, 1998, 2009, 2020] and min(GR[c], key=GR[c].get) == 1998)

# ---------- Thailand ----------
s, c = 'thailand', 'THA'; t = common(s, c, None)
uasc = [k for k, _ in sorted([(k, v[L]) for k, v in UN.items() if k in econ and L in v], key=lambda x: x[1])]
seaR = [k for k, _ in sorted([(k, G[k][L]) for k in SEA if L in G.get(k, {})], key=lambda x: -x[1])]
yrs = range(2021, L + 1)
expect(t, s, {'infl 2022': p1(INF[c][2022]), 'g1997': p1(abs(GR[c][1997])), 'g1998': p1(abs(GR[c][1998])), 'gmin': p1(min(GR[c][y] for y in yrs)), 'gmax': p1(max(GR[c][y] for y in yrs)),
              'u rank': ordn(uasc.index(c) + 1), 'rem rank': ordn(rank(REM, c))})
claim(s, 'deflation in 2025; earlier 2009, 2015, 2020', [y for y in INF[c] if INF[c][y] < 0][-4:] == [2009, 2015, 2020, L])
claim(s, '4th lowest unemployment', uasc.index(c) == 3)
claim(s, 'growth 0-3% since 2021; slower than five neighbours', all(0 < GR[c][y] < 3 for y in yrs) and all(GR[k][L] > GR[c][L] for k in ('IDN', 'MYS', 'PHL', 'SGP', 'VNM')))
claim(s, '29th, third in SE Asia; 1998 worst', rank(G, c) == 29 and seaR[:3] == ['IDN', 'SGP', c] and min(GR[c], key=GR[c].get) == 1998)
claim(s, 'remittances >2x 2015', REM[c][L] > 2 * REM[c][2015])

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
