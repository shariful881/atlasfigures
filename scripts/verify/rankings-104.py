# Run after `npm run build`: python3 scripts/verify/rankings-104.py
# Independent check of the inflation, unemployment and remittances rankings: reads the ORIGINAL World Bank zips
# (data/raw/wdi/) and UN WPP file, never the site's generated data, and confirms every ranking row, the CSVs,
# the figures in the text and the claims behind each sentence.
import csv, io, zipfile, gzip, re, html, sys, json

def wdi(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        n = z.namelist()
        lines = z.read([x for x in n if x.startswith('API_')][0]).decode('utf-8-sig').splitlines()
        meta = list(csv.DictReader(io.StringIO(z.read([x for x in n if x.startswith('Metadata_Country')][0]).decode('utf-8-sig'))))
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    return ({r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)} for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))},
            {m['Country Code']: m for m in meta if m['Region']})

INF, econ = wdi('FP.CPI.TOTL.ZG'); UN, _ = wdi('SL.UEM.TOTL.ZS'); REM, _ = wdi('BX.TRF.PWKR.CD.DT'); REMP, _ = wdi('BX.TRF.PWKR.DT.GD.ZS')
agg = lambda c: json.load(open(f'data/raw/wdi/{c}.metadata.json'))['source'][0]['concept'][0]['variable'][0]['metatype']
aggm = lambda c: next(x['value'] for x in agg(c) if x['id'] == 'Aggregationmethod')
pop = {}
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz', 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Variant'] == 'Medium' and r['Time'] == '2025' and r['LocTypeName'] == 'Country/Area' and r['ISO3_code']:
            pop[r['ISO3_code']] = round(float(r['TPopulation1July']) * 1000)

p1 = lambda v: f"{v:.1f}%"
usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion" if v >= 1e9 else f"${v/1e6:.1f} million"
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"
ok = 0; bad = []
def expect(text, k, v):
    global ok
    if v in text: ok += 1
    else: bad.append(f'{k}: {v} not on the page')
def claim(k, c):
    global ok
    if c: ok += 1; print(f'  ✓ claim: {k}')
    else: bad.append(f'claim false: {k}')
def load(slug):
    page = open(f'dist/rankings/{slug}/index.html').read()
    return page, html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S))))
def ranked(src, y): return sorted([(c, s[y]) for c, s in src.items() if c in econ and y in s], key=lambda x: -x[1])
def rows(page): return [(m[0], html.unescape(re.sub(r'<[^>]+>', '', m[1])).strip()) for m in re.findall(r'<tr data-iso3="([A-Z]+)".*?<td class="c-pop c-val"[^>]*>.*?<span class="n"[^>]*>(.*?)</span>', page, re.S)]
def check_rows(label, page, R, fmt):
    global ok
    got = rows(page)
    if len(got) != len(R): bad.append(f'{label}: {len(got)} rows ≠ {len(R)}')
    for i, ((c, v), (gc, gv)) in enumerate(zip(R, got)):
        if c == gc and gv == fmt(v): ok += 1
        else: bad.append(f'{label} row {i+1}: {gc} {gv} ≠ {c} {fmt(v)}')
def check_csv(slug, R, col):
    global ok
    lines = [l for l in open(f'dist/data/{slug}.csv').read().splitlines() if l and not l.startswith('#')]
    head = lines[0].split(','); r = list(csv.reader(lines[1:]))
    if len(r) != len(R): bad.append(f'{slug} CSV {len(r)} rows ≠ {len(R)}'); return
    for i, (f, (c, v)) in enumerate(zip(r, R)):
        if int(f[0]) == i + 1 and f[head.index('iso3')] == c and float(f[head.index(col)]) == v: ok += 1
        else: bad.append(f'{slug} CSV row {i+1}')

L = 2025
# ---------- inflation ----------
print('Inflation')
page, t = load('inflation-rate-by-country'); R = ranked(INF, L); N = len(R); rk = {c: i + 1 for i, (c, _) in enumerate(R)}
check_rows('inflation', page, R, p1); check_csv('inflation-rate-by-country', R, 'inflation_consumer_prices_pct')
vals = sorted(v for _, v in R)
for k, v in {'Iran': p1(R[0][1]), 'Turkey': p1(R[1][1]), 'Burundi': p1(R[2][1]), 'Sri Lanka': p1(R[-1][1]), 'Niger': p1(R[-2][1]), 'Chad': p1(R[-3][1]),
             'world median': p1(INF['WLD'][L]), 'median 2022': p1(INF['WLD'][2022]), 'Argentina 2024': p1(INF['ARG'][2024]), 'US 2024': p1(INF['USA'][2024]),
             'Sri Lanka 2022': p1(INF['LKA'][2022]), 'Bangladesh': p1(INF['BGD'][L]), 'Bangladesh rank': ordn(rk['BGD']), 'Pakistan': p1(INF['PAK'][L]), 'Nepal': p1(INF['NPL'][L]), 'India': p1(INF['IND'][L]),
             'double digit': f"{sum(1 for v in vals if v > 10)} economies had double-digit", 'at or below 3': f"{sum(1 for v in vals if v <= 3)} economies out of {N}", 'falling': f"{sum(1 for v in vals if v < 0)} saw prices fall",
             'not ranked': f"{sum(1 for c in econ if L not in INF.get(c, {}))} economies are absent"}.items():
    expect(t, k, v)
claim('world figure is the median', aggm('FP.CPI.TOTL.ZG') == 'Median')
claim('top three Iran, Turkey, Burundi, all above 30%, fourth below', [c for c, _ in R[:3]] == ['IRN', 'TUR', 'BDI'] and all(v > 30 for _, v in R[:3]) and R[3][1] < 30)
claim('bottom three Sri Lanka, Niger, Chad', [c for c, _ in R[-3:]] == ['TCD', 'NER', 'LKA'])
claim('Argentina highest in 2024; Argentina and US lack 2025', ranked(INF, 2024)[0][0] == 'ARG' and L not in INF['ARG'] and L not in INF['USA'])
claim('2022 median highest since 2008', INF['WLD'][2008] > INF['WLD'][2022] and all(INF['WLD'][y] < INF['WLD'][2022] for y in range(2009, L + 1) if y != 2022))
claim('South Asia order BGD > PAK > NPL > IND > LKA', [c for c, _ in R if c in ('BGD', 'PAK', 'NPL', 'IND', 'LKA')] == ['BGD', 'PAK', 'NPL', 'IND', 'LKA'])

# ---------- unemployment ----------
print('Unemployment')
page, t = load('unemployment-rate-by-country'); R = ranked(UN, L); N = len(R); rk = {c: i + 1 for i, (c, _) in enumerate(R)}
check_rows('unemployment', page, R, p1); check_csv('unemployment-rate-by-country', R, 'unemployment_pct_modelled_ilo')
za = UN['ZAF']; zmin = min(za, key=za.get)
giants = [c for c, _ in R if pop.get(c, 0) > 100e6]
for k, v in {'Eswatini': p1(R[0][1]), 'South Africa': p1(R[1][1]), 'Djibouti': p1(R[2][1]), 'Qatar': p1(R[-1][1]), 'Cambodia': p1(R[-2][1]), 'Niger': p1(R[-3][1]),
             'world': p1(UN['WLD'][L]), 'world 2020': p1(UN['WLD'][2020]), 'ZAF min': f"{p1(za[zmin])}, in {zmin}", 'giants count': f"Of the {len(giants)} nations",
             'Egypt': p1(UN['EGY'][L]), 'Vietnam': p1(UN['VNM'][L]), 'India': p1(UN['IND'][L]), 'Pakistan': p1(UN['PAK'][L]), 'Bangladesh': p1(UN['BGD'][L]), 'Bangladesh rank': ordn(rk['BGD']),
             'Spain': p1(UN['ESP'][L]), 'Germany': p1(UN['DEU'][L])}.items():
    expect(t, k, v)
claim('world figure is a weighted average', aggm('SL.UEM.TOTL.ZS') == 'Weighted average')
claim('seven of top ten in Sub-Saharan Africa', sum(1 for c, _ in R[:10] if econ[c]['Region'] == 'Sub-Saharan Africa') == 7)
claim('South Africa above 30% 2021–2025, below in 2020', all(za[y] > 30 for y in range(2021, L + 1)) and za[2020] < 30 and min(za) == 1991)
claim('world peaked 2020, eased every year since', max(UN['WLD'], key=UN['WLD'].get) == 2020 and all(UN['WLD'][y] < UN['WLD'][y - 1] for y in range(2021, L + 1)))
claim('Egypt highest, Vietnam lowest among 100M+', giants[0] == 'EGY' and giants[-1] == 'VNM')
claim('Spain almost three times Germany', 2.5 < UN['ESP'][L] / UN['DEU'][L] < 3)

# ---------- remittances ----------
print('Remittances')
page, t = load('remittances-by-country'); R = ranked(REM, L); N = len(R); P = ranked(REMP, L); rk = {c: i + 1 for i, (c, _) in enumerate(R)}
check_rows('remittances', page, R, lambda v: f"{round(v/1e6):,}"); check_csv('remittances-by-country', R, 'remittances_received_current_usd')
W = REM['WLD']; top10 = sum(v for _, v in R[:10])
for k, v in {'India': usd(R[0][1]), 'Mexico': usd(R[1][1]), 'France': usd(R[2][1]), 'world': usd(W[L]), 'world 2000': usd(W[2000]), 'top 10 share': p1(top10 / W[L] * 100),
             'India share': p1(R[0][1] / W[L] * 100), 'Tajikistan': p1(P[0][1]), 'Tonga': p1(P[1][1]), 'Nepal': p1(P[2][1]), 'over 10%': f"{sum(1 for _, v in P if v > 10)} economies received more than a tenth",
             'India % GDP': p1(REMP['IND'][L]), 'Mexico % GDP': p1(REMP['MEX'][L]), 'France % GDP': p1(REMP['FRA'][L]), 'Pakistan': usd(REM['PAK'][L]), 'Bangladesh': usd(REM['BGD'][L]),
             'Pakistan %': p1(REMP['PAK'][L]), 'Bangladesh %': p1(REMP['BGD'][L]), 'Ethiopia 2024': f"{usd(REM['ETH'][2024])}, 2024", 'India 100bn year': 'one hundred billion dollars in 2022'}.items():
    expect(t, k, v)
claim('world figure is a sum', aggm('BX.TRF.PWKR.CD.DT') == 'Sum')
claim('top seven order', [c for c, _ in R[:7]] == ['IND', 'MEX', 'FRA', 'PHL', 'EGY', 'PAK', 'BGD'])
claim('India more than twice Mexico; first above $100bn in 2022', R[0][1] > 2 * R[1][1] and min(y for y, v in REM['IND'].items() if v > 100e9) == 2022)
claim('Tajikistan, Tonga, Nepal most dependent', [c for c, _ in P[:3]] == ['TJK', 'TON', 'NPL'])
claim('top ten more than half; world more than seven times 2000', top10 / W[L] > 0.5 and W[L] > 7 * W[2000])
claim('Pakistan and Bangladesh ahead of China', rk['PAK'] < rk['CHN'] and rk['BGD'] < rk['CHN'])

print(f'\n{ok} checks matched the original World Bank / UN files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
