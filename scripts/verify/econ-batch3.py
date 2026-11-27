# Run after `npm run build`: python3 scripts/verify/econ-batch1.py
# Independent check of the economy pages for Pakistan, Nigeria, Indonesia, Brazil and Russia (task 108):
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

# ---------- Pakistan ----------
s, c = 'pakistan', 'PAK'; t = common(s, c, None)
ry, rv = last(REM, c); ny, nv = last(NET, c)
expect(t, s, {'infl 2023': p1(INF[c][2023]), 'infl 2022': p1(INF[c][2022]), 'infl 2024': p1(INF[c][2024]), 'rem 2015': usd(REM[c][2015]), 'rem %': p1(REMP[c][L]),
              'g2020': sp(GR[c][2020]), 'g2023': sp(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'pc rank': ordn(rank(PC, c)), 'rem rank': f"{ordn(rank(REM, c, ry))} largest"})
claim(s, 'GDP record', max(G[c], key=G[c].get) == L)
claim(s, 'falls only 2020, 2023', neg(c) == [2020, 2023] and min(GR[c]) == 1961)
claim(s, '2023 inflation series high from 1960', max(INF[c], key=INF[c].get) == 2023 and min(INF[c]) == 1960)
claim(s, 'inflation lowest since 2015', max(y for y in INF[c] if y < L and INF[c][y] < INF[c][L]) == 2015)
claim(s, 'remittances 6th, record, >2x 2015', rank(REM, c, ry) == 6 and ry == L and max(REM[c], key=REM[c].get) == L and 2 < rv / REM[c][2015] < 2.2)

# ---------- Nigeria ----------
s, c = 'nigeria', 'NGA'; t = common(s, c, None)
NA = ['DZA', 'EGY', 'LBY', 'MAR', 'TUN']
afr = [k for k, _ in sorted([(k, v[L]) for k, v in G.items() if k in econ and L in v and (econ[k]['Region'] == 'Sub-Saharan Africa' or k in NA)], key=lambda x: -x[1])]
ssa = [k for k, _ in sorted([(k, v[L]) for k, v in REM.items() if k in econ and L in v and econ[k]['Region'] == 'Sub-Saharan Africa'], key=lambda x: -x[1])]
pk = max(G[c], key=G[c].get)
expect(t, s, {'ZAF': usd(G['ZAF'][L]), 'EGY': usd(G['EGY'][L]), 'gdp 2022': usd(G[c][2022]), 'gdp 2024': usd(G[c][2024]), 'peak': usd(G[c][pk]),
              'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'infl 2024': p1(INF[c][2024]), 'rem %': p1(REMP[c][L]), 'pc rank': ordn(rank(PC, c))})
claim(s, 'third in Africa', afr[:3] == ['ZAF', 'EGY', c])
claim(s, 'peak 2019; 2024 less than half 2022, lowest since 2006', pk == 2019 and G[c][2024] < G[c][2022] / 2 and max(y for y in G[c] if y < 2024 and G[c][y] < G[c][2024]) == 2006)
claim(s, 'growth positive since 2021', all(GR[c][y] > 0 for y in range(2021, L + 1)))
claim(s, '2024 inflation highest since 1995; double digits since 2016', max(y for y in INF[c] if y < 2024 and INF[c][y] > INF[c][2024]) == 1995 and all(INF[c][y] > 10 for y in INF[c] if y >= 2016))
claim(s, 'largest SSA remittance receiver; 11th', ssa[0] == c and rank(REM, c) == 11)

# ---------- Indonesia ----------
s, c = 'indonesia', 'IDN'; t = common(s, c, None)
sea = ['BRN', 'KHM', 'IDN', 'LAO', 'MYS', 'MMR', 'PHL', 'SGP', 'THA', 'TLS', 'VNM']  # UN M49 South-eastern Asia
seaR = [k for k, _ in sorted([(k, G[k][L]) for k in sea if L in G.get(k, {})], key=lambda x: -x[1])]
expect(t, s, {'SGP': usd(G['SGP'][L]), 'ratio': f"{G[c][L] / G['SGP'][L]:.1f} times", 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]),
              'g1998': p1(abs(GR[c][1998])), 'pc 2000': whole(PC[c][2000]), 'pc rank': ordn(rank(PC, c))})
claim(s, '17th, largest in South-eastern Asia, Singapore second', rank(G, c) == 17 and seaR[:2] == [c, 'SGP'])
claim(s, 'first $1T in 2017', min(y for y in G[c] if G[c][y] >= 1e12) == 2017)
claim(s, 'pc above $5,000 first time', PC[c][L] >= 5000 and all(PC[c][y] < 5000 for y in PC[c] if y != L))
claim(s, 'growth 5.0-5.5 since 2022', all(5 <= GR[c][y] < 5.5 for y in range(2022, L + 1)))
claim(s, 'falls 1963, 1998, 2020', neg(c) == [1963, 1998, 2020] and min(GR[c]) == 1961)
claim(s, '1966 inflation >1000%, 2025 lowest since 2021', max(INF[c], key=INF[c].get) == 1966 and INF[c][1966] > 1000 and max(y for y in INF[c] if y < L and INF[c][y] < INF[c][L]) == 2021)

# ---------- Brazil ----------
s, c = 'brazil', 'BRA'; t = common(s, c, None)
lac = [k for k, _ in sorted([(k, v[L]) for k, v in G.items() if k in econ and L in v and econ[k]['Region'] == 'Latin America & Caribbean'], key=lambda x: -x[1])]
gp = max(G[c], key=G[c].get); pp = max(PC[c], key=PC[c].get)
expect(t, s, {'MEX': usd(G['MEX'][L]), 'peak': usd(G[c][gp]), 'pc peak': whole(PC[c][pp]), 'below': f"about {round((1 - G[c][L] / G[c][gp]) * 100)}%", 'pc below': f"about {round((1 - PC[c][L] / PC[c][pp]) * 100)}%",
              'unemp 2020': p1(UN[c][2020]), 'g2015': sp(GR[c][2015]), 'g2016': sp(GR[c][2016]), 'g2020': sp(GR[c][2020]), 'infl 2024': p1(INF[c][2024]), 'infl 2022': p1(INF[c][2022]), 'g2024': p1(GR[c][2024])})
claim(s, '11th, LAC first, Mexico second', rank(G, c) == 11 and lac[:2] == [c, 'MEX'])
claim(s, 'peaks 2011', gp == 2011 and pp == 2011)
claim(s, 'unemployment record low since 1991, down each year since 2020', min(UN[c], key=UN[c].get) == L and min(UN[c]) == 1991 and all(UN[c][y] > UN[c][y + 1] for y in range(2020, L)))
claim(s, 'declines since 2015: 2015, 2016, 2020', [y for y in neg(c) if y >= 2015] == [2015, 2016, 2020])
claim(s, '1990 inflation nearly 3,000%', max(INF[c], key=INF[c].get) == 1990 and 2900 < INF[c][1990] < 3000)

# ---------- Russia ----------
s, c = 'russia', 'RUS'; t = common(s, c, None)
expect(t, s, {'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'g2022': sp(GR[c][2022]), 'g1992': sp(GR[c][1992]), 'unemp 1998': p1(UN[c][1998]),
              'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'infl 2024': p1(INF[c][2024]), 'pc rank': ordn(rank(PC, c))})
claim(s, '8th, record GDP', rank(G, c) == 8 and max(G[c], key=G[c].get) == L)
claim(s, 'over $2T 2011-14 and 2022-25', sorted(y for y in G[c] if G[c][y] >= 2e12) == [2011, 2012, 2013, 2014, 2022, 2023, 2024, 2025])
claim(s, 'unemployment record low, down 5 years, 1998 high', min(UN[c], key=UN[c].get) == L and min(UN[c]) == 1991 and max(UN[c], key=UN[c].get) == 1998 and all(UN[c][y] > UN[c][y + 1] for y in range(2020, L)))
claim(s, 'inflation up two years, below 2022', INF[c][2023] < INF[c][2024] < INF[c][L] < INF[c][2022])
claim(s, '1992 worst since 1990', min(GR[c], key=GR[c].get) == 1992 and min(GR[c]) == 1990)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
