# Run after `npm run build`: python3 scripts/verify/telecom-114.py
# Independent check of the internet and mobile ranking pages (task 114): reads the ORIGINAL World Bank zips
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
NETA = wdi_agg('IT.NET.USER.ZS'); MOBA = wdi_agg('IT.CEL.SETS.P2'); SUBA = wdi_agg('IT.CEL.SETS'); BBA = wdi_agg('IT.NET.BBND.P2')
NET, econ = wdi('IT.NET.USER.ZS'); MOB, _ = wdi('IT.CEL.SETS.P2'); SUB, _ = wdi('IT.CEL.SETS'); BB, _ = wdi('IT.NET.BBND.P2')
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

# ---------- Internet users ----------
s = 'internet-users-by-country'; p, t = page(s); L = cov(NET); rk = order(NET, L)
claim('year 2024', L == 2024)
claim('rows = original', [(r[0], r[1]) for r in rows_of(p)] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == p1(NET[r[0]][L]) for r in rows_of(p)))
c = csv_rows(s); h = c[0]
claim('CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index('internet_users_pct_population')]) == NET[rk[i]][L] for i, r in enumerate(c[1:])))
W = NETA['WLD']
expect(s, t, {'world': p1(W[L]), 'w2005': p1(W[2005]), 'DNK': p1(NET['DNK'][L]), 'BDI': p1(NET['BDI'][L]), 'UGA': p1(NET['UGA'][L]), 'HIC': p1(NETA['HIC'][L]), 'LIC': p1(NETA['LIC'][L]), 'SSF': p1(NETA['SSF'][L]), 'SAS': p1(NETA['SAS'][L]),
              'BGD': p1(NET['BGD'][L]), 'IND': p1(NET['IND'][L]), 'PAK': p1(NET['PAK'][L]), 'USA': p1(NET['USA'][L]), 'CHN': p1(NET['CHN'][L]), 'BGD rank': f'{ordn(rk.index("BGD") + 1)} of {len(rk)}'})
claim('100%: ARE BHR SAU; DNK 4th', [x for x in rk if NET[x][L] >= 99.95] == ['ARE', 'BHR', 'SAU'] and rk[3] == 'DNK')
claim('BDI, UGA bottom, only two under 10; 11 under 20', rk[-2:] == ['UGA', 'BDI'] and sum(NET[x][L] < 10 for x in rk) == 2 and sum(NET[x][L] < 20 for x in rk) == 11)
claim('world passed half 2019', min(y for y, v in W.items() if v >= 50) == 2019)
claim('first above half: BGD 2024, IND 2022, PAK 2024', [min(y for y, v in NET[x].items() if v > 50) for x in ('BGD', 'IND', 'PAK')] == [2024, 2022, 2024])
claim('over 90 count shown', f'{sum(NET[x][L] >= 90 for x in rk)} economies reached 90%' in t)

# ---------- Mobile subscriptions ----------
s = 'mobile-subscriptions-by-country'; p, t = page(s); L = cov(MOB); rk = order(MOB, L); sk = order(SUB, L); bk = order(BB, L)
claim('year 2023', L == 2023)
claim('rows = original', [(r[0], r[1]) for r in rows_of(p)] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == f'{MOB[r[0]][L]:.1f}' for r in rows_of(p)))
c = csv_rows(s); h = c[0]
claim('CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index('mobile_subscriptions_per_100_people')]) == MOB[rk[i]][L] for i, r in enumerate(c[1:])))
bn = lambda v: f'{v / 1e9:.2f} billion'; mn = lambda v: f'{v / 1e6:.1f} million'
expect(s, t, {'world subs': bn(SUBA['WLD'][L]), 'world per100': f'{MOBA["WLD"][L]:.1f}', 'world bb': f'{BBA["WLD"][L]:.1f}', 'FJI': f'{MOB["FJI"][L]:.1f}', 'HKG': f'{MOB["HKG"][L]:.1f}', 'MNE': f'{MOB["MNE"][L]:.1f}', 'PNG': f'{MOB["PNG"][L]:.1f}',
              'CHN': bn(SUB['CHN'][L]), 'IND': bn(SUB['IND'][L]), 'USA': mn(SUB['USA'][L]), 'BGD': mn(SUB['BGD'][L]), 'BGD per100': f'{MOB["BGD"][L]:.1f}', 'BGD bb': f'{BB["BGD"][L]:.1f}', 'MCO bb': f'{BB["MCO"][L]:.1f}'})
claim('top FJI HKG MNE; PNG last', rk[:3] == ['FJI', 'HKG', 'MNE'] and rk[-1] == 'PNG')
claim('world > 100 since 2017', min(y for y, v in MOBA['WLD'].items() if v > 100) == 2017)
claim('subs: CHN IND USA; BGD 9th, PAK 10th', sk[:3] == ['CHN', 'IND', 'USA'] and sk[8:10] == ['BGD', 'PAK'])
claim('broadband MCO AND LIE FRA; NGA < 0.1', bk[:4] == ['MCO', 'AND', 'LIE', 'FRA'] and BB['NGA'][L] < 0.1)
claim('over-100 count shown', f'in {sum(MOB[x][L] > 100 for x in rk)} individual economies out of {len(rk)}' in t)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
