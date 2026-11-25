# Run after `npm run build`: python3 scripts/verify/econ-bangladesh.py
# Independent check: reads the ORIGINAL World Bank zips in data/raw/wdi/ and the original UN WPP file
# (never the site's generated data) and confirms every figure shown on the built Bangladesh economy page,
# its JSON-LD, its CSV and the economy hub. Prints each figure and where it was found.
import csv, io, zipfile, gzip, re, json, html, sys

def wdi(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        name = [n for n in z.namelist() if n.startswith('API_')][0]
        lines = z.read(name).decode('utf-8-sig').splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    out = {}
    for r in csv.DictReader(io.StringIO('\n'.join(lines[i:]))):
        out[r['Country Code']] = {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)}
    return out

G = wdi('NY.GDP.MKTP.CD'); PC = wdi('NY.GDP.PCAP.CD'); PPP = wdi('NY.GDP.PCAP.PP.CD'); GR = wdi('NY.GDP.MKTP.KD.ZG')
INF = wdi('FP.CPI.TOTL.ZG'); UN = wdi('SL.UEM.TOTL.ZS'); REM = wdi('BX.TRF.PWKR.CD.DT'); REMP = wdi('BX.TRF.PWKR.DT.GD.ZS'); NET = wdi('IT.NET.USER.ZS')
pop = {}
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz', 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['ISO3_code'] in ('BGD', 'PAK') and r['Variant'] == 'Medium' and r['Time'] == '2025':
            pop[r['ISO3_code']] = round(float(r['TPopulation1July']) * 1000)

usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion"
whole = lambda v: f"${round(v):,}"
p1 = lambda v: f"{v:.1f}%"
sp = lambda v: ('+' if round(v, 1) > 0 else '') + f"{v:.1f}%"
mil = lambda v: f"{v/1e6:.1f} million"

def text_of(path):
    page = open(path).read()
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S))))
    ld = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)]
    return page, t, json.dumps(ld, ensure_ascii=False)

page, text, ld = text_of('dist/economy/bangladesh/index.html')
B = 'BGD'; L = max(G[B]); assert L == 2025, L
avg = sum(GR[B][y] for y in range(2010, 2020)) / 10
exp = {
    'GDP 2025': usd(G[B][L]), 'GDP 1972': usd(G[B][1972]), 'share of world GDP 2025': p1(G[B][L] / G['WLD'][L] * 100),
    'Pakistan GDP 2025': usd(G['PAK'][L]), 'Pakistan population 2025 (UN)': mil(pop['PAK']), 'Bangladesh population 2025 (UN)': mil(pop['BGD']),
    'GDP per person 2025': whole(PC[B][L]), 'GDP per person 2019': whole(PC[B][2019]), 'GDP per person 2024': whole(PC[B][2024]),
    'India GDP per person 2019': whole(PC['IND'][2019]), 'India GDP per person 2024': whole(PC['IND'][2024]), 'India GDP per person 2025': whole(PC['IND'][L]),
    'PPP 2025': f"Int${round(PPP[B][L]):,}", 'India PPP 2025': f"Int${round(PPP['IND'][L]):,}",
    'times since 2000': f"{PC[B][L]/PC[B][2000]:.1f} times",
    'growth 2025': p1(GR[B][L]), 'growth 2025 signed': sp(GR[B][L]), 'average growth 2010–2019': p1(avg), 'growth 2019': p1(GR[B][2019]),
    'growth 1971': sp(GR[B][1971]), 'growth 1972': sp(GR[B][1972]), 'South Asia growth 2025': p1(GR['SAS'][L]),
    'inflation 2025': p1(INF[B][L]), 'inflation 2024': p1(INF[B][2024]),
    'remittances 2025': usd(REM[B][L]), 'remittances 2023': usd(REM[B][2023]), 'remittances % GDP 2025': p1(REMP[B][L]),
    'unemployment 2025': p1(UN[B][L]), 'internet 2024': p1(NET[B][2024]),
}
# Facts behind the sentences (re-derived from the original files)
facts = {
    'no contraction 1976–2025': all(GR[B][y] > 0 for y in range(1976, L + 1)) and GR[B][1975] < 0,
    '1971 and 1972 deepest falls': sorted(GR[B], key=GR[B].get)[:2] == [1972, 1971],
    'growth 2025 slowest since 2020': all(GR[B][y] > GR[B][L] for y in range(2021, L)) and GR[B][2020] < GR[B][L],
    'growth peak since 1990 in 2019': max(range(1990, L + 1), key=lambda y: GR[B][y]) == 2019,
    'ahead of India 2019–2024 only (since 2010)': [y for y in range(2010, L + 1) if PC[B][y] > PC['IND'][y]] == list(range(2019, 2025)),
    'inflation 2024 highest since 2011': INF[B][2011] > INF[B][2024] and all(INF[B][y] < INF[B][2024] for y in range(2012, 2024)),
    'inflation 5–6% every year 2016–2021': all(5 < INF[B][y] < 6 for y in range(2016, 2022)),
    'remittances 2025 a record': all(v < REM[B][L] for y, v in REM[B].items() if y != L),
    'remittances > 1.5 × 2023': REM[B][L] / REM[B][2023] > 1.5,
    'remittance share highest since 2015': REMP[B][2015] > REMP[B][L] and all(REMP[B][y] < REMP[B][L] for y in range(2016, L)),
    'internet first year above half': NET[B][2024] > 50 and NET[B][2023] < 50,
    'Bangladesh GDP > Pakistan, Pakistan more people': G[B][L] > G['PAK'][L] and pop['PAK'] > pop['BGD'],
}
ok = 0; bad = []
for k, v in exp.items():
    if v in text: ok += 1; print(f'  ✓ {k}: {v}')
    else: bad.append(f'{k}: {v} not on the page')
for k, v in facts.items():
    if v: ok += 1; print(f'  ✓ claim: {k}')
    else: bad.append(f'claim false: {k}')
# JSON-LD numbers shown on the page
for n in re.findall(r'\d[\d,]*(?:\.\d+)?', ' '.join(re.findall(r'"(?:headline|description|name|text)": "([^"]*)"', ld))):
    if n not in text: bad.append(f'JSON-LD number {n} not on the page')
ok += 1
# table: every row against the original files
for tr in re.findall(r'<tr[^>]*data-year="(\d{4})"[^>]*>(.*?)</tr>', page, re.S):
    y = int(tr[0]); cells = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr[1], re.S)]
    want = [f"{G[B][y]/1e9:.1f}" if y in G[B] else '–', whole(PC[B][y]) if y in PC[B] else '–', sp(GR[B][y]) if y in GR[B] else '–', p1(INF[B][y]) if y in INF[B] else '–', p1(REMP[B][y]) if y in REMP[B] else '–']
    if cells == want: ok += 1
    else: bad.append(f'table {y}: {cells} ≠ {want}')
# CSV: every value
csvl = [l for l in open('dist/data/bangladesh-economy.csv').read().splitlines() if l and not l.startswith('#')]
cols = [G, PC, PPP, GR, INF, UN, REM, REMP, NET]
for l in csvl[1:]:
    f = l.split(','); y = int(f[0])
    for i, src in enumerate(cols):
        got = f[i + 1]; want = src[B].get(y)
        if (want is None and got != '') or (want is not None and float(got) != want): bad.append(f'CSV {y} column {i+1}')
        else: ok += 1
# hub: world figures
hub, htext, _ = text_of('dist/economy/index.html')
for k, v in {'world GDP 2025': usd(G['WLD'][L]), 'world GDP per person 2025': whole(PC['WLD'][L]), 'world growth 2025': p1(GR['WLD'][L])}.items():
    if v in htext: ok += 1; print(f'  ✓ hub {k}: {v}')
    else: bad.append(f'hub {k}: {v} missing')
print(f'\n{ok} checks matched the original World Bank / UN files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
