# Run after `npm run build`: python3 scripts/verify/migration-113.py
# Independent check of the immigrant population and immigrant percentage ranking pages (task 113): reads the ORIGINAL World Bank zips
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

from decimal import Decimal, ROUND_HALF_UP
hu = lambda v: Decimal(repr(v)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)  # JavaScript Math.round
comma = lambda v: f'{hu(v):,}'
mil = lambda v: f'{v / 1e6:.1f} million'
MS, econ = wdi('SM.POP.TOTL'); MP, _ = wdi('SM.POP.TOTL.ZS'); MSA = wdi_agg('SM.POP.TOTL'); MPA = wdi_agg('SM.POP.TOTL.ZS')
for x in ('SM.POP.TOTL', 'SM.POP.TOTL.ZS'):
    claim(f'{x}: licence CC BY-4.0', '"CC BY-4.0"' in open(f'data/raw/wdi/{x}.metadata.json').read())
claim('aggregation: Sum / Weighted average', 'Sum' in open('data/raw/wdi/SM.POP.TOTL.metadata.json').read() and 'Weighted average' in open('data/raw/wdi/SM.POP.TOTL.ZS.metadata.json').read())
L = 2024; W = MSA['WLD']; WP = MPA['WLD']
cell = {'immigrant-population-by-country': lambda v: comma(v), 'immigrant-percentage-by-country': lambda v: p1(v)}
for s, S, col in (('immigrant-population-by-country', MS, 'international_migrant_stock'), ('immigrant-percentage-by-country', MP, 'international_migrant_stock_pct_population')):
    p, t = page(s); rk = order(S, L); rows = rows_of(p)
    claim(f'{s}: year {L} = latest world', max((MSA if S is MS else MPA)['WLD']) == L)
    claim(f'{s}: rows = original ({len(rk)})', len(rows) == len(rk) and [(r[0], r[1]) for r in rows] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == cell[s](S[r[0]][L]) for r in rows))
    c = csv_rows(s); h = c[0]
    claim(f'{s}: CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index(col)]) == S[rk[i]][L] for i, r in enumerate(c[1:])))
    trs = re.findall(r'<tr[^>]*data-iso3="(\w+)"[^>]*>(.*?)</tr>', p, re.S)
    cells = {k: [html.unescape(x).strip() for x in re.findall(r'<td[^>]*>([^<]*)</td>', m)][-2:] for k, m in trs}
    if S is MS: claim(f'{s}: share and 2000 cells', all(cells[k] == [p1(MP[k][L]) if L in MP.get(k, {}) else '–', comma(MS[k][2000]) if 2000 in MS[k] else '–'] for k in cells))
    else: claim(f'{s}: count and 1990 cells', all(cells[k] == [comma(MS[k][L]) if L in MS.get(k, {}) else '–', p1(MP[k][1990]) if 1990 in MP[k] else '–'] for k in cells))

# ---------- Immigrant population ----------
s = 'immigrant-population-by-country'; p, t = page(s); rk = order(MS, L)
gain = sorted([k for k in rk if 2000 in MS[k]], key=lambda k: MS[k][2000] - MS[k][L])
top10 = sum(MS[k][L] for k in rk[:10])
expect(s, t, {'world': mil(W[L]), 'world1990': mil(W[1990]), 'share': p1(WP[L]), 'share1990': p1(WP[1990]), 'one in': f'one person in {hu(100 / WP[L])}', 'USA': mil(MS['USA'][L]), 'USA%': p1(MS['USA'][L] / W[L] * 100), 'top10': p1(top10 / W[L] * 100),
              'DEU': mil(MS['DEU'][L]), 'SAU': mil(MS['SAU'][L]), 'GBR': mil(MS['GBR'][L]), 'FRA': mil(MS['FRA'][L]), 'USA gain': f'+{mil(MS["USA"][L] - MS["USA"][2000])}', 'ESP': mil(MS['ESP'][L]), 'ESP2000': mil(MS['ESP'][2000]), 'COL': mil(MS['COL'][L]),
              'RUS': mil(MS['RUS'][L]), 'RUS2000': mil(MS['RUS'][2000]), 'IND': mil(MS['IND'][L]), 'IND2000': mil(MS['IND'][2000]), 'IND%': p1(MP['IND'][L]), 'IND rank': ordn(rk.index('IND') + 1), 'BGD': mil(MS['BGD'][L]), 'BGDn': comma(MS['BGD'][L]), 'BGD2000': mil(MS['BGD'][2000]),
              'BGD%': p1(MP['BGD'][L]), 'BGD rank': ordn(rk.index('BGD') + 1), 'PAK': mil(MS['PAK'][L]), 'PAK%': p1(MP['PAK'][L]), 'N': f'{len(rk)} countries and areas'})
claim('pop: order; US > next three; nearly doubled; biggest gains US SAU GBR, falls RUS IND; Spain x4+, Russia down about a third; Colombia ~100k in 2000; BGD rise mostly after 2015',
      rk[:5] == ['USA', 'DEU', 'SAU', 'GBR', 'FRA'] and MS['USA'][L] > sum(MS[k][L] for k in rk[1:4]) and 1.95 < W[L] / W[1990] < 2 and gain[:3] == ['USA', 'SAU', 'GBR'] and gain[-1] == 'RUS' and gain[-2] == 'IND'
      and MS['ESP'][L] / MS['ESP'][2000] > 4 and 0.6 < MS['RUS'][L] / MS['RUS'][2000] < 0.7 and 95e3 < MS['COL'][2000] < 115e3 and MS['BGD'][L] - MS['BGD'][2015] > MS['BGD'][2015] - MS['BGD'][2000] and MS['IND'][2000] > MS['IND'][L])

# ---------- Immigrant percentage ----------
s = 'immigrant-percentage-by-country'; p, t = page(s); rk = order(MP, L)
rise = sorted([k for k in rk if 2000 in MP[k]], key=lambda k: -(MP[k][L] - MP[k][2000]))
qpk = max(MP['QAT'], key=MP['QAT'].get)
expect(s, t, {'QAT': p1(MP['QAT'][L]), 'ARE': p1(MP['ARE'][L]), 'KWT': p1(MP['KWT'][L]), 'KWT rank': ordn(rk.index('KWT') + 1), 'world': p1(WP[L]), 'HIC': p1(MPA['HIC'][L]), 'LMY': p1(MPA['LMY'][L]), 'SAS': p1(MPA['SAS'][L]), 'qpk': f'{p1(MP["QAT"][qpk])} in {qpk}',
              'Q1990': p1(MP['QAT'][1990]), 'USA': p1(MP['USA'][L]), 'USA1990': p1(MP['USA'][1990]), 'GBR': p1(MP['GBR'][L]), 'DEU': p1(MP['DEU'][L]), 'CAN': p1(MP['CAN'][L]), 'AUS': p1(MP['AUS'][L]), 'SAU': p1(MP['SAU'][L]),
              'ESP1990': p1(MP['ESP'][1990]), 'ESP2000': p1(MP['ESP'][2000]), 'ESP': p1(MP['ESP'][L]), 'CHL2000': p1(MP['CHL'][2000]), 'CHL': p1(MP['CHL'][L]), 'COL2015': p1(MP['COL'][2015]), 'COL': p1(MP['COL'][L]),
              'BGD': p1(MP['BGD'][L]), 'BGD1990': p1(MP['BGD'][1990]), 'BGD rank': ordn(rk.index('BGD') + 1), 'BGDn': mil(MS['BGD'][L]), 'IND': p1(MP['IND'][L]), 'CHN': p1(MP['CHN'][L]), 'CUB': p1(MP['CUB'][L]),
              'over50': f'{sum(1 for k in rk if MP[k][L] > 50)} countries and areas', 'under1': f'{sum(1 for k in rk if MP[k][L] < 1)} countries and areas', 'N': f'all {len(rk)} places'})
claim('pct: order; Qatar & UAE about three in four; Qatar peak 2015; biggest rises Aruba Malta; lowest six; BGD more than doubled',
      rk[:3] == ['QAT', 'ARE', 'MCO'] and 73 < MP['ARE'][L] < 77 and 73 < MP['QAT'][L] < 77 and qpk == 2015 and rise[:2] == ['ABW', 'MLT'] and rk[-6:] == ['CHN', 'MDG', 'MMR', 'PHL', 'CUB', 'MAF'] and MP['BGD'][L] > 2 * MP['BGD'][1990])

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
