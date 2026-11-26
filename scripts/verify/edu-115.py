# Run after `npm run build`: python3 scripts/verify/edu-115.py
# Independent check of the literacy and education-spending ranking pages (task 115): reads the ORIGINAL World Bank zips
# (data/raw/wdi/), never the site's generated data; confirms every row, the CSVs, the figures and claims.
import csv, io, zipfile, gzip, re, html, sys, json

def wdi(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        n = z.namelist()
        lines = z.read([x for x in n if x.startswith('API_')][0]).decode('utf-8-sig').splitlines()
        meta = list(csv.DictReader(io.StringIO(z.read([x for x in n if x.startswith('Metadata_Country')][0]).decode('utf-8-sig'))))
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    return ({r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)} for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))},
            {m['Country Code']: m for m in meta if m['Region']})


def wdi_agg(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        n = z.namelist(); lines = z.read([x for x in n if x.startswith('API_')][0]).decode('utf-8-sig').splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    return {r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)} for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))}
ok = 0; bad = []
def claim(k, c):
    global ok
    if c: ok += 1
    else: bad.append(f'claim false: {k}')
def page(slug):
    p = open(f'dist/rankings/{slug}/index.html', encoding='utf-8').read()
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', p, flags=re.S))))
    return p, t
def expect(slug, t, d):
    global ok
    for k, v in d.items():
        if v in t: ok += 1
        else: bad.append(f'{slug}: {k} "{v}" not on the page')
def cov(S):
    from collections import Counter
    n = Counter(y for k, s in S.items() if k in econ for y in s); mx = max(n.values())
    return max(y for y, c in n.items() if c >= 0.8 * mx)
order = lambda S, y: [k for k, _ in sorted(((k, v[y]) for k, v in S.items() if k in econ and y in v), key=lambda x: (-x[1], x[0]))]
rows_of = lambda p: [(m.group(1), int(m.group(2)), html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).strip()) for m in re.finditer(r'<tr[^>]*data-iso3="(\w+)"[^>]*data-rank="(\d+)"[^>]*>.*?<td class="[^"]*c-val[^"]*"[^>]*>(.*?)</td>', p, re.S)]
csv_rows = lambda slug: list(csv.reader([l for l in open(f'dist/data/{slug}.csv', encoding='utf-8').read().splitlines() if l and not l.startswith('#')]))
p1 = lambda v: f'{v:.1f}%'
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"

LA, econ = wdi('AG.LND.TOTL.K2'); FA, _ = wdi('AG.LND.FRST.K2'); FP, _ = wdi('AG.LND.FRST.ZS')
LAA = wdi_agg('AG.LND.TOTL.K2'); FAA = wdi_agg('AG.LND.FRST.K2'); FPA = wdi_agg('AG.LND.FRST.ZS')
from decimal import Decimal, ROUND_HALF_UP
hu = lambda v, q='1': Decimal(repr(v)).quantize(Decimal(q), rounding=ROUND_HALF_UP)  # JavaScript-style half-up rounding
LIT, econ = wdi('SE.ADT.LITR.ZS'); EDU, _ = wdi('SE.XPD.TOTL.GD.ZS'); LITA = wdi_agg('SE.ADT.LITR.ZS'); EDUA = wdi_agg('SE.XPD.TOTL.GD.ZS')
for x in ('SE.ADT.LITR.ZS', 'SE.XPD.TOTL.GD.ZS'):
    claim(f'{x}: licence CC BY-4.0', '"CC BY-4.0"' in open(f'data/raw/wdi/{x}.metadata.json').read())
def latest_rank(S, since):
    r = [(k, max(y for y in s if y >= since)) for k, s in S.items() if k in econ and any(y >= since for y in s)]
    return sorted(((k, y, S[k][y]) for k, y in r), key=lambda z: (-z[2], z[0]))
f1 = lambda v: f'{hu(v, "0.1")}%'
for s, S, since, col in (('literacy-rate-by-country', LIT, 2015, 'adult_literacy_pct_ages_15_plus'), ('education-spending-by-country', EDU, 2020, 'government_education_expenditure_pct_gdp')):
    p, t = page(s); rk = latest_rank(S, since); rows = rows_of(p)
    claim(f'{s}: rows = original latest values ({len(rk)})', len(rows) == len(rk) and [(r[0], r[1]) for r in rows] == [(k, i + 1) for i, (k, _, _) in enumerate(rk)] and all(r[2] == f1(v) for r, (_, _, v) in zip(rows, rk)))
    trs = re.findall(r'<tr[^>]*data-iso3="(\w+)"[^>]*>(.*?)</tr>', p, re.S)
    claim(f'{s}: year cells', all(f'>{y}<' in m for (k, m), (_, y, _) in zip(trs, rk)))
    c = csv_rows(s); h = c[0]
    claim(f'{s}: CSV = original (value and year)', len(c) - 1 == len(rk) and all(r[2] == rk[i][0] and int(r[h.index('year')]) == rk[i][1] and float(r[h.index(col)]) == rk[i][2] for i, r in enumerate(c[1:])))

# ---------- Literacy ----------
s = 'literacy-rate-by-country'; p, t = page(s); rk = latest_rank(LIT, 2015); W = LITA['WLD']; L = max(W)
d = {k: (y, v) for k, y, v in rk}
hic_all = sum(1 for k in econ if econ[k]['IncomeGroup'] == 'High income'); hic = sum(1 for k in d if econ[k]['IncomeGroup'] == 'High income')
expect(s, t, {'world': f1(W[L]), '1975': f1(W[1975]), 'SSA': f1(LITA['SSF'][L]), 'SAS': f1(LITA['SAS'][L]), 'TCD': f1(d['TCD'][1]), 'NER': f1(d['NER'][1]), 'AFG': f1(d['AFG'][1]),
              'BGD': f1(d['BGD'][1]), 'BGD1981': f1(LIT['BGD'][1981]), 'IND': f1(d['IND'][1]), 'PAK': f1(d['PAK'][1]), 'BGD rank': ordn([k for k, _, _ in rk].index('BGD') + 1), 'hic': f'only {hic} of the {hic_all}',
              'n2024': f'only {sum(1 for k in d if d[k][0] == L)} have one', 'N': f'{len(rk)} countries', 'u50': f'{sum(1 for k in d if d[k][1] < 50)} countries are below 50%', '99': f'{sum(1 for k in d if d[k][1] >= 99)} countries report', '995': f'{sum(1 for k in d if d[k][1] >= 99.5)} countries'})
claim('literacy: Chad lowest, then Niger/Mali, Afghanistan; under 50% all SSA but AFG; world rising, slower since 2000', [k for k, _, _ in rk[-1:]] == ['TCD'] and set(k for k, _, _ in rk[-3:-1]) == {'NER', 'MLI'} and rk[-4][0] == 'AFG' and all(econ[k]['Region'] == 'Sub-Saharan Africa' or k == 'AFG' for k in d if d[k][1] < 50) and (W[2000] - W[1975]) / 25 > 2 * (W[L] - W[2000]) / (L - 2000))
claim('literacy: weighted average; definition', 'Weighted average' in open('data/raw/wdi/SE.ADT.LITR.ZS.metadata.json').read() and 'read and write with understanding' in open('data/raw/wdi/SE.ADT.LITR.ZS.metadata.json').read())

# ---------- Education spending ----------
s = 'education-spending-by-country'; p, t = page(s); rk = latest_rank(EDU, 2020); d = {k: (y, v) for k, y, v in rk}
vals = sorted(v for _, _, v in rk); n = len(vals); med = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2
order_ = [k for k, _, _ in rk]
expect(s, t, {'median': f1(med), 'ge4': f'{sum(1 for v in vals if v >= 4)} spend 4%', 'HIC': f1(EDUA['HIC'][max(EDUA['HIC'])]), 'LIC': f1(EDUA['LIC'][max(EDUA['LIC'])]), 'KIR': f1(d['KIR'][1]), 'TUV': f1(d['TUV'][1]), 'FSM': f1(d['FSM'][1]),
              'BGD': f1(d['BGD'][1]), 'BGD rank': ordn(order_.index('BGD') + 1), 'PAK': f1(d['PAK'][1]), 'LKA': f1(d['LKA'][1]), 'IND': f1(d['IND'][1]), 'BTN': f1(d['BTN'][1]), 'USA': f1(d['USA'][1]), 'GBR': f1(d['GBR'][1]),
              'SWE': f'{ordn(order_.index("SWE") + 1)} at {f1(d["SWE"][1])}', 'NGA': f1(d['NGA'][1]), 'ZWE': f1(d['ZWE'][1]), 'PNG': f1(d['PNG'][1])})
claim('spending: KIR TUV FSM top; SOM ~0 then NGA ZWE PNG; BGD never above 2.7% since 2000; median aggregation', order_[:3] == ['KIR', 'TUV', 'FSM'] and order_[-4:] == ['PNG', 'ZWE', 'NGA', 'SOM'] and d['SOM'][1] < 0.001 and all(v < 2.7 for y, v in EDU['BGD'].items() if y >= 2000) and 'Median' in open('data/raw/wdi/SE.XPD.TOTL.GD.ZS.metadata.json').read())
claim('spending: HIC and LIC medians are 2022; US and UK 2021', max(EDUA['HIC']) == 2022 and max(EDUA['LIC']) == 2022 and d['USA'][0] == 2021 and d['GBR'][0] == 2021)

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
