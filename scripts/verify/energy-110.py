# Run after `npm run build`: python3 scripts/verify/energy-110.py
# Independent check of the two energy ranking pages (task 110): reads the ORIGINAL Global Carbon Project and
# Ember files in data/raw/energy/ with Python's csv module (never the site's generated data) and confirms every
# ranking row, the CSVs, every figure in the text and the claim behind each sentence.
import csv, gzip, html, re, sys

RAW = 'data/raw/energy'
un = set()
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz', 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['ISO3_code'] and r['Time'] == '2025' and r['Variant'] == 'Medium':
            un.add(r['ISO3_code'])
un.add('XKX')  # Kosovo: in the site's UN list via the WPP index (code XKX); GCB uses KSV

co2, pc = {}, {}
for r in csv.DictReader(open(f'{RAW}/GCB2026v11_MtCO2_flat.csv', encoding='utf-8')):
    iso = r['ISO 3166-1 alpha-3']; iso = 'XKX' if iso == 'KSV' else iso
    if iso == 'WLD' or iso in un:
        if r['Total']: co2.setdefault(iso, {})[int(r['Year'])] = float(r['Total'])
        if r['Per Capita'] and float(r['Per Capita']) != 0: pc.setdefault(iso, {})[int(r['Year'])] = float(r['Per Capita'])
E = {}
for r in csv.DictReader(open(f'{RAW}/ember-yearly-electricity-global.csv', encoding='utf-8')):
    iso = r['ISO 3 code'] if r['Area type'] == 'Country or economy' else ('WORLD' if r['Area'] == 'World' else None)
    if not iso or (iso != 'WORLD' and iso not in un): continue
    src, y = r['Electricity source'], int(r['Year'])
    for col, k in (('Generation (TWh)', 'gen'), ('Share of generation (%)', 'share')):
        if r[col] != '': E.setdefault((iso, src, k), {})[y] = float(r[col])

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
def rows_of(p):
    return [(m.group(1), int(m.group(2)), html.unescape(re.sub(r'<[^>]+>', '', m.group(3))).strip()) for m in re.finditer(r'<tr[^>]*data-iso3="(\w+)"[^>]*data-rank="(\d+)"[^>]*>.*?<td class="[^"]*c-val[^"]*"[^>]*>(.*?)</td>', p, re.S)]
def csv_rows(slug):
    return list(csv.reader([l for l in open(f'dist/data/{slug}.csv', encoding='utf-8').read().splitlines() if l and not l.startswith('#')]))
order = lambda d, y: [k for k, _ in sorted(((k, v[y]) for k, v in d.items() if k not in ('WLD', 'WORLD') and y in v), key=lambda x: (-x[1], x[0]))]
p1 = lambda v: f'{v:.1f}%'
bt = lambda mt: f'{mt / 1000:.2f} billion tonnes' if mt >= 1000 else f'{mt:.1f} million tonnes'

# ---------- CO2 ----------
s = 'co2-emissions-by-country'; p, t = page(s); L = 2025
rk = order(co2, L); W = co2['WLD'][L]; Wpc = pc['WLD'][L]; pcr = order(pc, L)
rows = rows_of(p)
claim('CO2 rows = original order and values', [(r[0], r[1]) for r in rows] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == f'{co2[r[0]][L]:,.1f}' for r in rows))
c = csv_rows(s); h = c[0]
claim('CO2 CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index('co2_million_tonnes')]) == co2[rk[i]][L] for i, r in enumerate(c[1:])))
top3 = sum(co2[x][L] for x in rk[:3]); top10 = sum(co2[x][L] for x in rk[:10])
expect(s, t, {'CHN': bt(co2['CHN'][L]), 'USA': bt(co2['USA'][L]), 'IND': bt(co2['IND'][L]), 'world': bt(W), 'CHN share': p1(co2['CHN'][L] / W * 100), 'top3': p1(top3 / W * 100), 'top10': p1(top10 / W * 100),
              'QAT pc': f'{pc["QAT"][L]:.1f} tonnes', 'USA pc': f'{pc["USA"][L]:.1f}', 'world pc': f'{Wpc:.1f}', 'BGD': bt(co2['BGD'][L]), 'BGD pc': f'{pc["BGD"][L]:.2f} tonnes', 'world change': p1((W / co2['WLD'][L - 1] - 1) * 100),
              'USA change': f'{(co2["USA"][L] / co2["USA"][L - 1] - 1) * 100:.1f}%', 'USA peak': bt(co2['USA'][2005])})
claim('top five CHN USA IND RUS JPN', rk[:5] == ['CHN', 'USA', 'IND', 'RUS', 'JPN'])
claim('China > next four combined', co2['CHN'][L] > sum(co2[x][L] for x in rk[1:5]))
claim('world record and > sum of countries', max(co2['WLD'], key=co2['WLD'].get) == L and W > sum(co2[x][L] for x in rk))
claim('per person QAT BRN BHR KWT', pcr[:4] == ['QAT', 'BRN', 'BHR', 'KWT'])
claim('US > 3x world pc; China above, India below', pc['USA'][L] > 3 * Wpc and pc['CHN'][L] > Wpc > pc['IND'][L])
claim('Germany lowest since 1950, Japan since 1987', max(y for y, v in co2['DEU'].items() if y < L and v < co2['DEU'][L]) == 1950 and max(y for y, v in co2['JPN'].items() if y < L and v < co2['JPN'][L]) == 1987)
claim('US peak 2005; China passed US 2006', max(co2['USA'], key=co2['USA'].get) == 2005 and min(y for y in co2['CHN'] if y in co2['USA'] and co2['CHN'][y] > co2['USA'][y]) == 2006)
claim('Bangladesh 38th total, pc rank shown', rk.index('BGD') == 37 and f'{pcr.index("BGD") + 1}th of {len(pcr)}' in t)

# ---------- Renewables ----------
s = 'renewable-electricity-by-country'; p, t = page(s); L = 2024
share = {k[0]: v for k, v in E.items() if k[1] == 'Renewables' and k[2] == 'share'}
rk = order(share, L)
rows = rows_of(p)
claim('renewables rows = original order and values (capped at 100)', [(r[0], r[1]) for r in rows] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == p1(min(share[r[0]][L], 100)) for r in rows))
c = csv_rows(s); h = c[0]
claim('renewables CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index('renewables_share_of_generation_pct')]) == share[rk[i]][L] for i, r in enumerate(c[1:])))
g = lambda iso, src='Total generation', k='gen', y=L: E.get((iso, src, k), {}).get(y)
W = share['WORLD']; Wws = E[('WORLD', 'Wind and solar', 'share')]
cn = g('CHN', 'Renewables') / g('WORLD', 'Renewables') * 100
big = [x for x in rk if (g(x) or 0) >= 100]
near = [x for x in rk if share[x][L] >= 99.95]
expect(s, t, {'world': p1(W[L]), 'world 2025': p1(W[L + 1]), 'ws': p1(Wws[L]), 'ws 2015': p1(Wws[2015]), 'NOR': p1(share['NOR'][L]), 'BRA': p1(share['BRA'][L]), 'CHN': p1(share['CHN'][L]), 'USA': p1(share['USA'][L]),
              'IND': p1(share['IND'][L]), 'China of world': p1(cn), 'China TWh': f'{g("CHN", "Renewables"):,.1f} TWh', 'BGD': p1(share['BGD'][L]), 'BGD gen': f'{g("BGD"):,.1f} TWh', 'ISL other': p1(g('ISL', 'Other renewables', 'share')), 'DNK ws': p1(g('DNK', 'Wind and solar', 'share'))})
claim('seven at 100%', near == ['ALB', 'COD', 'ISL', 'PRY', 'BTN', 'ETH', 'NPL'])
claim('hydro > half in all seven', all(g(x, 'Hydro', 'share') > 50 for x in near))
claim('big systems: NOR BRA SWE CAN top; SAU BGD IRQ bottom under 3%', big[:4] == ['NOR', 'BRA', 'SWE', 'CAN'] and big[-3:] == ['SAU', 'BGD', 'IRQ'] and all(share[x][L] < 3 for x in big[-3:]) and f'{len(big)} countries' in t)
claim('wind and solar: LSO DJI DNK', order({k[0]: v for k, v in E.items() if k[1] == 'Wind and solar' and k[2] == 'share'}, L)[:3] == ['LSO', 'DJI', 'DNK'])
claim('world ws more than tripled since 2015; share rising every year since 2008', Wws[L] > 3 * Wws[2015] and all(W[y] >= W[y - 1] for y in range(2008, L + 1)))
claim('China ~ a third of world renewable power', 33 < cn < 34)

print(f'{ok} checks matched the original Global Carbon Project and Ember files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
