# Run after `npm run build`: python3 scripts/verify/econ-batch1.py
# Independent check of the economy pages for Germany, Japan, South Korea, France and Australia (task 106):
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

# ---------- Germany ----------
s, c = 'germany', 'DEU'; t = common(s, c, None)
ahead = [y for y in G[c] if y in G['JPN'] and G[c][y] > G['JPN'][y]]
expect(t, s, {'Japan GDP': usd(G['JPN'][L]), 'g2023': sp(GR[c][2023]), 'g2024': sp(GR[c][2024]), 'g2009': sp(GR[c][2009]), 'g2020': sp(GR[c][2020]),
              'unemp 2022': p1(UN[c][2022]), 'unemp 2010': p1(UN[c][2010]), 'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'pc rank': ordn(rank(PC, c))})
claim(s, 'third; ahead of Japan 2023-25, before that 1971', rank(G, c) == 3 and [y for y in ahead if y > 1971] == [2023, 2024, 2025] and 1971 in ahead)
claim(s, 'first back-to-back fall since 2002-03', all(not (GR[c][y] < 0 and GR[c].get(y + 1, 1) < 0) for y in GR[c] if 2003 < y < 2023) and GR[c][2002] < 0 and GR[c][2003] < 0)
claim(s, 'weakest G7 growth', all(GR[k][L] > GR[c][L] for k in g7 if k != c))
claim(s, '2022 inflation highest since 1974', highest_since(INF, c, 2022) == 1974)
claim(s, 'second-lowest G7 unemployment after Japan', [k for k in g7 if UN[k][L] < UN[c][L]] == ['JPN'])

# ---------- Japan ----------
s, c = 'japan', 'JPN'; t = common(s, c, None)
pk = max(G[c], key=G[c].get); defl = len([y for y in INF[c] if 1995 <= y <= 2021 and INF[c][y] < 0])
expect(t, s, {'peak': usd(G[c][pk]), 'fall': f"about {round((1 - G[c][L] / G[c][pk]) * 100)}%", 'infl 2023': p1(INF[c][2023]), 'KOR pc': whole(PC['KOR'][L]), 'defl years': f"{defl} separate years"})
claim(s, 'fourth, peak 2012', rank(G, c) == 4 and pk == 2012)
claim(s, 'prices fell in 15 years 1995-2021', defl == 15)
claim(s, 'above 2% since 2022, 2023 highest since 1981', all(INF[c][y] > 2 for y in (2022, 2023, 2024, L)) and highest_since(INF, c, 2023) == 1981)
claim(s, 'Korea ahead per person since 2023, PPP since 2016', [y for y in PC[c] if PC['KOR'].get(y, 0) > PC[c][y]] == [2023, 2024, 2025] and min(y for y in PPP[c] if PPP['KOR'].get(y, 0) > PPP[c][y]) == 2016)
claim(s, 'lowest G7 unemployment', all(UN[k][L] > UN[c][L] for k in g7 if k != c))
claim(s, 'latest contraction 2024', neg(c)[-1] == 2024)

# ---------- South Korea ----------
s, c = 'south-korea', 'KOR'; t = common(s, c, None)
f20 = min(y for y in PC[c] if PC[c][y] >= 20000)
expect(t, s, {'pc 1960': whole(PC[c][1960]), 'pc 1990': whole(PC[c][1990]), 'first 20k': f"in {f20}", 'JPN pc': whole(PC['JPN'][L]), 'JPN GDP': usd(G['JPN'][L]),
              'ratio': f"{G['JPN'][L] / G[c][L]:.1f} times", 'g1998': sp(GR[c][1998]), 'g2020': sp(GR[c][2020]), 'g2024': p1(GR[c][2024]), 'infl 2022': p1(INF[c][2022])})
claim(s, 'more than 200-fold', PC[c][L] / PC[c][1960] > 200)
claim(s, 'falls only 1980, 1998, 2020', neg(c) == [1980, 1998, 2020] and min(GR[c]) == 1961)
claim(s, 'slowest since 2020', all(GR[c][y] > GR[c][L] for y in range(2021, L)) and GR[c][2020] < GR[c][L])
claim(s, 'internet above 97%', last(NET, c)[1] > 97)
claim(s, 'internet rank', f"{ordn(rank(NET, c, last(NET, c)[0]))} among" in t)

# ---------- France ----------
s, c = 'france', 'FRA'; t = common(s, c, None)
ry, rv = last(REM, c)
expect(t, s, {'g2020': sp(GR[c][2020]), 'g2021': p1(GR[c][2021]), 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'unemp 2015': p1(UN[c][2015]),
              'unemp 2022': p1(UN[c][2022]), 'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'infl 2024': p1(INF[c][2024]), 'rem rank': f"the {ordn(rank(REM, c, ry))} largest"})
claim(s, 'seventh', rank(G, c) == 7)
claim(s, '2020 worst since 1961, 2021 best since 1969', min(GR[c], key=GR[c].get) == 2020 and min(GR[c]) == 1961 and highest_since(GR, c, 2021) == 1969)
claim(s, 'growth slower each year since 2021', GR[c][2021] > GR[c][2022] > GR[c][2023] > GR[c][2024] > GR[c][L])
claim(s, 'highest G7 unemployment', all(UN[k][L] < UN[c][L] for k in g7 if k != c))
claim(s, 'unemployment low 2022, high 2015 since 2010, rising since', min(UN[c], key=UN[c].get) == 2022 and max((y for y in UN[c] if y >= 2010), key=UN[c].get) == 2015 and UN[c][2022] < UN[c][2023] < UN[c][2024] < UN[c][L])
claim(s, 'lowest inflation of G7 with 2025 figure; US none', all(INF[k][L] > INF[c][L] for k in g7 if k != c and L in INF[k]) and L not in INF['USA'])
claim(s, 'remittances 3rd, up >40% since 2020', rank(REM, c, ry) == 3 and ry == L and rv > REM[c][2020] * 1.4)

# ---------- Australia ----------
s, c = 'australia', 'AUS'; t = common(s, c, None)
pk = max(PC[c], key=PC[c].get)
expect(t, s, {'pc rank': ordn(rank(PC, c)), 'g2020': p1(abs(GR[c][2020])), 'g1983': sp(GR[c][1983]), 'g1991': sp(GR[c][1991]), 'g2022': p1(GR[c][2022]), 'peak': whole(PC[c][pk]),
              'unemp 2023': p1(UN[c][2023]), 'unemp 1991': p1(UN[c][1991]), 'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'infl 2024': p1(INF[c][2024])})
claim(s, '15th by GDP, 12th per person', rank(G, c) == 15 and rank(PC, c) == 12)
claim(s, 'falls only 1983, 1991, 2020', neg(c) == [1983, 1991, 2020] and min(GR[c]) == 1961)
claim(s, 'pc peak 2013, still below', pk == 2013 and PC[c][L] < PC[c][pk])
claim(s, '2023 unemployment lowest since 1991', min(UN[c], key=UN[c].get) == 2023 and min(UN[c]) == 1991 and UN[c][L] > UN[c][2023])
claim(s, '2022 inflation highest since 1990', highest_since(INF, c, 2022) == 1990)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
