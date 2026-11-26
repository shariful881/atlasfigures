# Run after `npm run build`: python3 scripts/verify/geo-119.py
# Independent check of the land-area and forest-area ranking pages (task 119): reads the ORIGINAL World Bank zips
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
def cell(v):
    d = hu(v, '0.1')
    return f'{int(d):,}' if d == int(d) else f'{d:,}'
mkm = lambda v: f'{v / 1e6:.1f} million km²'
km = lambda v: f'{int(hu(v)):,} km²'
for x in ('AG.LND.TOTL.K2', 'AG.LND.FRST.K2', 'AG.LND.FRST.ZS'):
    claim(f'{x}: licence CC BY-4.0', '"CC BY-4.0"' in open(f'data/raw/wdi/{x}.metadata.json').read())

for s, S, col in (('land-area-by-country', LA, 'land_area_sq_km'), ('forest-area-by-country', FA, 'forest_area_sq_km')):
    p, t = page(s); L = max((LAA if S is LA else FAA)['WLD']); rk = order(S, L)
    claim(f'{s}: year 2023 = latest world total', L == 2023)
    rows = rows_of(p)
    claim(f'{s}: rows = original ({len(rk)})', len(rows) == len(rk) and [(r[0], r[1]) for r in rows] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == cell(S[r[0]][L]) for r in rows))
    c = csv_rows(s); h = c[0]
    claim(f'{s}: CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index(col)]) == S[rk[i]][L] for i, r in enumerate(c[1:])))
    claim(f'{s}: unranked = Channel Islands (last 2021) + places never reported', [k for k in econ if k not in rk and S.get(k)] == ['CHI'] and max(S['CHI']) == 2021)

# ---------- Land area ----------
s = 'land-area-by-country'; p, t = page(s); L = 2023; rk = order(LA, L); W = LAA['WLD'][L]
sh = lambda v: v / W * 100
REG = ['ECS', 'EAS', 'SSF', 'LCN', 'NAC', 'MEA', 'SAS']
expect(s, t, {'RUS': mkm(LA['RUS'][L]), 'CHN': mkm(LA['CHN'][L]), 'USA': mkm(LA['USA'][L]), 'CAN': mkm(LA['CAN'][L]), 'BRA': mkm(LA['BRA'][L]), 'AUS': mkm(LA['AUS'][L]), 'IND': mkm(LA['IND'][L]),
              'world': mkm(W), 'RUS share': f'{sh(LA["RUS"][L]):.1f}%', 'top6': f'{sh(sum(LA[x][L] for x in rk[:6])):.1f}%', 'over1m': f'{sum(1 for x in rk if LA[x][L] >= 1e6)} countries have more than a million',
              'BGD': km(LA['BGD'][L]), 'BGD rank': ordn(rk.index('BGD') + 1), 'MMR': km(LA['MMR'][L]), 'MCO': f'{LA["MCO"][L]:.1f}', 'GIB': cell(LA['GIB'][L]), 'NRU': cell(LA['NRU'][L]), 'TUV': cell(LA['TUV'][L]),
              'N': f'of {len(rk)}', 'ECS': mkm(LAA['ECS'][L]), 'SAS': mkm(LAA['SAS'][L]), 'SAS%': f'{sh(LAA["SAS"][L]):.1f}%'})
for r in REG: expect(s, t, {r: f'{int(hu(LAA[r][L])):,}', r + '%': f'{sh(LAA[r][L]):.1f}%'})
claim('land: order RUS CHN USA CAN BRA AUS IND; six above 7m; MCO GIB NRU TUV smallest', rk[:7] == ['RUS', 'CHN', 'USA', 'CAN', 'BRA', 'AUS', 'IND'] and all(LA[x][L] > 7e6 for x in rk[:6]) and LA['IND'][L] < 3e6 and rk[-4:] == ['TUV', 'NRU', 'GIB', 'MCO'])
claim('land: China a little under three-fifths of Russia; India ~23x Bangladesh; Myanmar ~5x', 0.55 < LA['CHN'][L] / LA['RUS'][L] < 0.6 and round(LA['IND'][L] / LA['BGD'][L]) == 23 and round(LA['MMR'][L] / LA['BGD'][L]) == 5)
claim('land: regions add up to world; ECS largest, SAS smallest', abs(sum(LAA[r][L] for r in REG) - W) < W * 0.001 and max(REG, key=lambda r: LAA[r][L]) == 'ECS' and min(REG, key=lambda r: LAA[r][L]) == 'SAS')
claim('land: definition excludes inland water bodies', 'excluding area under inland water bodies' in open('data/raw/wdi/AG.LND.TOTL.K2.metadata.json').read())
claim('land: share column = value / world', all(f'{LA[x][L] / W * 100:.2f}%' in html.unescape(m) for x, m in zip(rk, re.findall(r'<tr[^>]*data-iso3="\w+"[^>]*>(.*?)</tr>', p, re.S))))

# ---------- Forest area ----------
s = 'forest-area-by-country'; p, t = page(s); L = 2023; B = 2000; rk = order(FA, L); W = FAA['WLD'][L]; sk = order(FP, L)
ch = sorted(((x, FA[x][L] - FA[x][B]) for x in rk if B in FA[x]), key=lambda z: (z[1], z[0]))
sumB = sum(FA[x][B] for x, _ in ch); sumD = sum(d for _, d in ch)
expect(s, t, {'world': mkm(W), 'world%': p1(FPA['WLD'][L]), 'top5': p1(sum(FA[x][L] for x in rk[:5]) / W * 100), 'RUS': mkm(FA['RUS'][L]), 'BRA': mkm(FA['BRA'][L]), 'CAN': mkm(FA['CAN'][L]),
              'n both': f'{len(ch)} places', 'loss': km(-sumD), 'loss%': p1(abs(sumD / sumB * 100)), 'BRA loss': km(-ch[0][1]), 'BRA%': p1(abs(ch[0][1] / FA['BRA'][B] * 100)), 'COD': km(-ch[1][1]), 'AGO': km(-ch[2][1]),
              'CHN gain': km(ch[-1][1]), 'CHN%': p1(ch[-1][1] / FA['CHN'][B] * 100), 'BRA 1990': mkm(FA['BRA'][1990]), 'FSM': p1(FP['FSM'][L]), 'SUR': p1(FP['SUR'][L]), 'GAB': p1(FP['GAB'][L]),
              'LAC': p1(FPA['LCN'][L]), 'MENA': p1(FPA['MEA'][L]), 'BGD%': p1(FP['BGD'][L]), 'BGD2000%': p1(FP['BGD'][B]), 'BGD km': km(FA['BGD'][L]), 'IND%': p1(FP['IND'][L]), 'IND2000%': p1(FP['IND'][B]), 'BTN': p1(FP['BTN'][L]), 'N': f'{len(rk)} countries and areas'})
claim('forest: RUS BRA CAN USA CHN; Russia about a fifth', rk[:5] == ['RUS', 'BRA', 'CAN', 'USA', 'CHN'] and round(FA['RUS'][L] / W * 100) == 21)
claim('forest: losses BRA COD AGO, gains CHN RUS CAN; Brazil lost more than China gained', [x for x, _ in ch[:3]] == ['BRA', 'COD', 'AGO'] and [x for x, _ in ch[-3:]] == ['CAN', 'RUS', 'CHN'] and -ch[0][1] > ch[-1][1])
claim('forest: FSM SUR GAB top shares, all three above 91%; GIB MCO NRU zero', sk[:3] == ['FSM', 'SUR', 'GAB'] and FP['GAB'][L] > 91 and sorted(x for x in sk if FP[x][L] == 0) == ['GIB', 'MCO', 'NRU'])
claim('forest: Brazil smaller every year since 1990', all(FA['BRA'][y] < FA['BRA'][y - 1] for y in range(1991, L + 1)))
claim('forest: Bhutan highest share in South Asia', max((x for x in sk if econ[x]['Region'] == 'South Asia'), key=lambda x: FP[x][L]) == 'BTN')
claim('forest: LAC highest and MENA lowest region share', max(['ECS', 'EAS', 'SSF', 'LCN', 'NAC', 'MEA', 'SAS'], key=lambda r: FPA[r][L]) == 'LCN' and min(['ECS', 'EAS', 'SSF', 'LCN', 'NAC', 'MEA', 'SAS'], key=lambda r: FPA[r][L]) == 'MEA')
claim('forest: no 2000 figure for SSD SRB MNE (and 4 others)', all(B not in FA[x] for x in ('SSD', 'SRB', 'MNE')) and len(rk) - len(ch) == 7)
sgn = lambda v: ('+' if v > 0 else '−' if v < 0 else '') + f'{int(hu(abs(v))):,}'
claim('forest: change cells = 2023 minus 2000', all((sgn(FA[x][L] - FA[x][B]) if B in FA[x] else '–') in html.unescape(m) for x, m in zip(rk, re.findall(r'<tr[^>]*data-iso3="\w+"[^>]*>(.*?)</tr>', p, re.S))))
claim('forest: definition 5 m trees, 10% canopy, 0.5 ha', all(w in open('data/raw/wdi/AG.LND.FRST.K2.metadata.json').read() for w in ('5 meters', '10 percent', '0.5 hectares')))

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
