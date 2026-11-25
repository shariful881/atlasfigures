# Run after `npm run build`: python3 scripts/verify/rankings-gdp.py
# Independent check of /rankings/gdp-by-country/ and /rankings/gdp-per-capita-by-country/: reads the ORIGINAL
# World Bank zips (data/raw/wdi/) and UN WPP file, never the site's generated data, and confirms every ranking
# row, the CSVs, every figure in the text and the claims behind each sentence.
import csv, io, zipfile, gzip, re, json, html, sys

def wdi(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        names = z.namelist()
        lines = z.read([n for n in names if n.startswith('API_')][0]).decode('utf-8-sig').splitlines()
        meta = list(csv.DictReader(io.StringIO(z.read([n for n in names if n.startswith('Metadata_Country')][0]).decode('utf-8-sig'))))
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    out = {r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)} for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))}
    return out, {m['Country Code']: m for m in meta if m['Region']}

G, econ = wdi('NY.GDP.MKTP.CD'); PC, _ = wdi('NY.GDP.PCAP.CD'); PPP, _ = wdi('NY.GDP.PCAP.PP.CD'); GR, _ = wdi('NY.GDP.MKTP.KD.ZG')
pop = {}
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz', 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Variant'] == 'Medium' and r['Time'] == '2025' and r['LocTypeName'] == 'Country/Area' and r['ISO3_code']:
            pop[r['ISO3_code']] = round(float(r['TPopulation1July']) * 1000)

usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion" if v >= 1e9 else f"${v/1e6:.1f} million"
whole = lambda v: f"${round(v):,}"
p1 = lambda v: f"{v:.1f}%"
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"
ok = 0; bad = []
def expect(text, k, v):
    global ok
    if v in text: ok += 1; print(f'  ✓ {k}: {v}')
    else: bad.append(f'{k}: {v} not on the page')
def claim(k, cond):
    global ok
    if cond: ok += 1; print(f'  ✓ claim: {k}')
    else: bad.append(f'claim false: {k}')
def load(path):
    page = open(path).read()
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S))))
    return page, t
def ranked(src, y): return sorted([(c, s[y]) for c, s in src.items() if c in econ and y in s], key=lambda x: -x[1])
def rows(page): return [(m[0], html.unescape(re.sub(r'<[^>]+>', '', m[1])).strip()) for m in re.findall(r'<tr data-iso3="([A-Z]+)".*?<td class="c-pop c-val"[^>]*>.*?<span class="n"[^>]*>(.*?)</span>', page, re.S)]
def check_csv(path, want, col):
    global ok
    lines = [l for l in open(path).read().splitlines() if l and not l.startswith('#')]
    head = lines[0].split(','); r = list(csv.reader(lines[1:]))
    if len(r) != len(want): bad.append(f'{path}: {len(r)} rows ≠ {len(want)}'); return
    for i, (f, (c, v)) in enumerate(zip(r, want)):
        if int(f[0]) == i + 1 and f[head.index('iso3')] == c and float(f[head.index(col)]) == v: ok += 1
        else: bad.append(f'{path} row {i+1}')

L = 2025; W = G['WLD'][L]
# ---------- GDP ----------
print('GDP by country')
page, text = load('dist/rankings/gdp-by-country/index.html')
R = ranked(G, L); N = len(R)
got = rows(page)
for i, ((c, v), (gc, gv)) in enumerate(zip(R, got)):
    if c == gc and gv == f"{v/1e9:,.1f}": ok += 1
    else: bad.append(f'GDP row {i+1}: page {gc} {gv} ≠ {c} {v/1e9:,.1f}')
if len(got) != N: bad.append(f'GDP rows {len(got)} ≠ {N}')
check_csv('dist/data/gdp-by-country.csv', R, 'gdp_current_usd')
top10 = sum(v for _, v in R[:10])
ratio = {y: G['CHN'][y] / G['USA'][y] * 100 for y in range(1990, L + 1)}
both = [c for c, _ in R if 2000 in G[c]]
r2000 = {c: i + 1 for i, c in enumerate(sorted(both, key=lambda c: -G[c][2000]))}; rnow = {c: i + 1 for i, c in enumerate(both)}
afr = [(c, v) for c, v in R if econ[c]['Region'] == 'Sub-Saharan Africa' or c in ('DZA', 'EGY', 'LBY', 'MAR', 'TUN')]
rk = {c: i + 1 for i, (c, _) in enumerate(R)}
for k, v in {'US GDP': usd(R[0][1]), 'China GDP': usd(R[1][1]), 'world GDP': usd(W), 'top 10 share': p1(top10 / W * 100), 'US+China share': p1((R[0][1] + R[1][1]) / W * 100),
             'India GDP (5th place value)': usd(R[5][1]), 'Germany GDP': usd(R[2][1]), 'trillion club': f"{sum(1 for _, v in R if v >= 1e12)} economies passed one trillion",
             'China/US 2000': p1(ratio[2000]), 'China/US peak 2021': p1(ratio[2021]), 'China/US 2025': p1(ratio[L]), 'economies both years': f"{len(both)} economies with figures for both years",
             'South Africa': usd(afr[0][1]), 'Egypt': usd(afr[1][1]), 'Nigeria': usd(afr[2][1]), 'Algeria': usd(afr[3][1]), 'South Africa world rank': ordn(rk['ZAF']),
             'Bangladesh': f"Bangladesh is {ordn(rk['BGD'])} at {usd(G['BGD'][L])}", 'Pakistan': f"Pakistan {ordn(rk['PAK'])} at {usd(G['PAK'][L])}", 'India rank': f"India is {ordn(rk['IND'])}",
             'Tuvalu': usd(R[-1][1]), 'ranked count': f"All {N}"}.items():
    expect(text, k, v)
claim('US 1st, China 2nd, then DEU JPN GBR IND', [c for c, _ in R[:6]] == ['USA', 'CHN', 'DEU', 'JPN', 'GBR', 'IND'])
claim('China/US peaked in 2021 (since 1990)', max(ratio, key=ratio.get) == 2021)
claim('ranks 2000→2025: CHN 6→2, IND 13→6, IDN up 10, RUS 20→8, JPN 2→4, MEX 9→14', (r2000['CHN'], rnow['CHN'], r2000['IND'], rnow['IND'], r2000['RUS'], rnow['RUS'], r2000['JPN'], rnow['JPN'], r2000['MEX'], rnow['MEX']) == (6, 2, 13, 6, 20, 8, 2, 4, 9, 14) and r2000['IDN'] - rnow['IDN'] == 10)
claim('UAE latest GDP year 2024, Cuba/Syria/Yemen not ranked', max(G['ARE']) == L - 1 and all(L not in G.get(c, {}) for c in ('CUB', 'SYR', 'YEM')))
claim('Tuvalu smallest', R[-1][0] == 'TUV')

# ---------- GDP per capita ----------
print('GDP per capita by country')
page, text = load('dist/rankings/gdp-per-capita-by-country/index.html')
R = ranked(PC, L); N = len(R); P = ranked(PPP, L); prk = {c: i + 1 for i, (c, _) in enumerate(P)}; rk = {c: i + 1 for i, (c, _) in enumerate(R)}
got = rows(page)
for i, ((c, v), (gc, gv)) in enumerate(zip(R, got)):
    if c == gc and gv == whole(v): ok += 1
    else: bad.append(f'per-capita row {i+1}: page {gc} {gv} ≠ {c} {whole(v)}')
if len(got) != N: bad.append(f'per-capita rows {len(got)} ≠ {N}')
check_csv('dist/data/gdp-per-capita-by-country.csv', R, 'gdp_per_person_current_usd')
wa = PC['WLD'][L]
above = [c for c, v in R if v > wa]
below_pop = sum(pop.get(c, 0) for c, v in R if v < wa); all_pop = sum(pop.get(c, 0) for c, _ in R)
for k, v in {'Luxembourg': whole(R[0][1]), 'Ireland': whole(R[1][1]), 'Switzerland': whole(R[2][1]), 'Burundi': whole(R[-1][1]), 'Central African Rep.': whole(R[-2][1]), 'Madagascar': whole(R[-3][1]),
             'world average': whole(wa), 'above average': f"only {len(above)} of the {N}", 'gap times': f"{round(R[0][1]/R[-1][1])} times", 'share of people below': p1(below_pop / all_pop * 100),
             'US': f"{ordn(rk['USA'])} overall at {whole(PC['USA'][L])}", 'China 2025': whole(PC['CHN'][L]), 'China 2000': whole(PC['CHN'][2000]), 'Singapore PPP': f"Int${round(P[0][1]):,}",
             'Bangladesh ranks': f"from {ordn(rk['BGD'])} at market exchange rates to {ordn(prk['BGD'])} at PPP", 'India ranks': f"India ranks {ordn(rk['IND'])} in US dollars and {ordn(prk['IND'])} at PPP"}.items():
    expect(text, k, v)
claim('LUX, IRL, CHE, SGP, ISL top five', [c for c, _ in R[:5]] == ['LUX', 'IRL', 'CHE', 'SGP', 'ISL'])
claim('USA highest among 20M+ people', [c for c, _ in R if pop.get(c, 0) > 20e6][0] == 'USA')
claim('Burundi, CAF, Madagascar bottom three', [c for c, _ in R[-3:]] == ['MDG', 'CAF', 'BDI'])
claim('bottom twenty mostly Sub-Saharan Africa', sum(1 for c, _ in R[-20:] if econ[c]['Region'] == 'Sub-Saharan Africa') > 10)
claim('China under world average now, under a fifth in 2000', PC['CHN'][L] < wa and PC['CHN'][2000] / PC['WLD'][2000] < 0.2)
claim('Monaco and Liechtenstein not ranked, latest figures above 3rd place', L not in PC['MCO'] and L not in PC['LIE'] and PC['MCO'][max(PC['MCO'])] > R[2][1] and PC['LIE'][max(PC['LIE'])] > R[2][1])

print(f'\n{ok} checks matched the original World Bank / UN files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
