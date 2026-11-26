# Run after `npm run build`: python3 scripts/verify/health-116.py
# Independent check of the child and maternal mortality ranking pages (task 116): reads the ORIGINAL World Bank zips
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
U5A = wdi_agg('SH.DYN.MORT'); INFA = wdi_agg('SP.DYN.IMRT.IN'); MMA = wdi_agg('SH.STA.MMRT')
U5, econ = wdi('SH.DYN.MORT'); INF, _ = wdi('SP.DYN.IMRT.IN'); MM, _ = wdi('SH.STA.MMRT')
f1 = lambda v: f'{v:.1f}'
SSA = lambda k: econ[k]['Region'] == 'Sub-Saharan Africa'

# ---------- Child mortality ----------
s = 'child-mortality-by-country'; p, t = page(s); L = max(U5A['WLD']); rk = order(U5, L)
claim('year 2024 = latest world year; every economy with data has 2024', L == 2024 and all(L in U5[k] for k in U5 if k in econ and U5[k]))
claim('rows = original', [(r[0], r[1]) for r in rows_of(p)] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == f1(U5[r[0]][L]) for r in rows_of(p)))
c = csv_rows(s); h = c[0]
claim('CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index('under5_mortality_per_1000_live_births')]) == U5[rk[i]][L] and float(r[h.index('infant_mortality_per_1000_live_births')]) == INF[rk[i]][L] for i, r in enumerate(c[1:])))
W = U5A['WLD']
expect(s, t, {'world': f1(W[L]), 'w1990': f1(W[1990]), 'inf': f1(INFA['WLD'][L]), 'ssf': f1(U5A['SSF'][L]), 'fall': f"{round((1 - W[L] / W[1990]) * 100)}%",
              'NGA': f1(U5['NGA'][L]), 'NER': f1(U5['NER'][L]), 'SOM': f1(U5['SOM'][L]), 'SMR': f1(U5['SMR'][L]), 'EST': f1(U5['EST'][L]), 'LUX': f1(U5['LUX'][L]),
              'USA': f1(U5['USA'][L]), 'GBR': f1(U5['GBR'][L]), 'CHN': f1(U5['CHN'][L]), 'BGD': f1(U5['BGD'][L]), 'BGD1990': f1(U5['BGD'][1990]), 'BGD fall': f"{round((1 - U5['BGD'][L] / U5['BGD'][1990]) * 100)}%",
              'IND': f1(U5['IND'][L]), 'PAK': f1(U5['PAK'][L]), 'PAK rank': ordn(rk.index('PAK') + 1), 'N': str(len(rk))})
claim('top NGA NER SOM; bottom SMR EST LUX (asc)', rk[:3] == ['NGA', 'NER', 'SOM'] and rk[-3:] == ['LUX', 'EST', 'SMR'])
claim('top 20 all SSA', all(SSA(x) for x in rk[:20]))
claim('world up 2021-22, down 2023-24', W[2021] > W[2020] and W[2022] > W[2021] and W[2023] < W[2022] and W[2024] < W[2023])
claim('most deaths in first year; BGD below world, IND lower, PAK above', INFA['WLD'][L] > W[L] / 2 and U5['BGD'][L] < W[L] and U5['IND'][L] < U5['BGD'][L] and U5['PAK'][L] > W[L])

# ---------- Maternal mortality ----------
s = 'maternal-mortality-by-country'; p, t = page(s); L = max(MMA['WLD']); rk = order(MM, L)
claim('year 2023 = latest world year; all have 2023', L == 2023 and all(L in MM[k] for k in MM if k in econ and MM[k]))
claim('rows = original', [(r[0], r[1]) for r in rows_of(p)] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == f'{int(MM[r[0]][L]):,}' for r in rows_of(p)))
c = csv_rows(s); h = c[0]
claim('CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index('maternal_deaths_per_100000_live_births')]) == MM[rk[i]][L] for i, r in enumerate(c[1:])))
W = MMA['WLD']; g = lambda x, y=L: str(int(MM[x][y]))
rose = sum(1 for x in rk if 2000 in MM[x] and MM[x][L] > MM[x][2000])
expect(s, t, {'world': str(int(W[L])), 'w2000': str(int(W[2000])), 'w2021': str(int(W[2021])), 'w2022': str(int(W[2022])), 'ssf': str(int(MMA['SSF'][L])), 'sas': str(int(MMA['SAS'][L])),
              'fall': f"{round((1 - W[L] / W[2000]) * 100)}%", 'NGA': g('NGA'), 'TCD': g('TCD'), 'CAF': g('CAF'), 'AFG': g('AFG'), 'AFG rank': ordn(rk.index('AFG') + 1),
              'USA': g('USA'), 'USA2000': g('USA', 2000), 'GBR': g('GBR'), 'BGD': g('BGD'), 'BGD2000': g('BGD', 2000), 'BGD fall': f"{round((1 - MM['BGD'][L] / MM['BGD'][2000]) * 100)}%",
              'IND': g('IND'), 'PAK': g('PAK'), 'AUS': g('AUS'), 'rose': f'higher in {rose} places'})
claim('NGA, TCD, then CAF & SSD tied; 19 of top 20 SSA, AFG the other', rk[0] == 'NGA' and rk[1] == 'TCD' and set(rk[2:4]) == {'CAF', 'SSD'} and MM['CAF'][L] == MM['SSD'][L] and sum(SSA(x) for x in rk[:20]) == 19 and [x for x in rk[:20] if not SSA(x)] == ['AFG'])
claim('lowest NOR BLR at 1; AUS ISR POL at 2', set(rk[-2:]) == {'NOR', 'BLR'} and MM['NOR'][L] == MM['BLR'][L] == 1 and set(rk[-5:-2]) == {'AUS', 'ISR', 'POL'} and all(MM[x][L] == 2 for x in ('AUS', 'ISR', 'POL')))
claim('2021 spike above 2020, 2022 below 2020; US up since 2000 and > 2x UK; SAS below world', W[2021] > W[2020] and W[2022] < W[2020] and MM['USA'][L] > MM['USA'][2000] and MM['USA'][L] > 2 * MM['GBR'][L] and MMA['SAS'][L] < W[L])

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
