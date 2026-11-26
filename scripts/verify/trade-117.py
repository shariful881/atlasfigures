# Run after `npm run build`: python3 scripts/verify/trade-117.py
# Independent check of the exports and imports ranking pages (task 117): reads the ORIGINAL World Bank zips
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
EXA = wdi_agg('NE.EXP.GNFS.CD'); IMA = wdi_agg('NE.IMP.GNFS.CD'); EXPA = wdi_agg('NE.EXP.GNFS.ZS'); IMPA = wdi_agg('NE.IMP.GNFS.ZS')
EX, econ = wdi('NE.EXP.GNFS.CD'); IM, _ = wdi('NE.IMP.GNFS.CD'); EXP, _ = wdi('NE.EXP.GNFS.ZS'); IMP, _ = wdi('NE.IMP.GNFS.ZS')
def usd(v):
    a = abs(v)
    return f"${a/1e12:.2f} trillion" if a >= 1e12 else f"${a/1e9:.1f} billion" if a >= 1e9 else f"${a/1e6:.1f} million"
bnc = lambda v: f'{v / 1e9:,.1f}'

for s, S, O, P, col in (('exports-by-country', EX, IM, EXP, 'exports_goods_services_current_usd'), ('imports-by-country', IM, EX, IMP, 'imports_goods_services_current_usd')):
    p, t = page(s); L = cov(S); rk = order(S, L)
    claim(f'{s}: year 2024 by 80% coverage', L == 2024)
    rows = rows_of(p)
    claim(f'{s}: rows = original', len(rows) == len(rk) and [(r[0], r[1]) for r in rows] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == bnc(S[r[0]][L]) for r in rows))
    c = csv_rows(s); h = c[0]
    claim(f'{s}: CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index(col)]) == S[rk[i]][L] for i, r in enumerate(c[1:])))
    claim(f'{s}: UAE 2023, Qatar 2022, Nigeria only 1960 unranked', max(S['ARE']) == 2023 and max(S['QAT']) == 2022 and list(S['NGA']) == [1960])

# ---------- Exports ----------
s = 'exports-by-country'; p, t = page(s); L = 2024; rk = order(EX, L); sk = order(EXP, L)
W = EXA['WLD']; top10 = sum(EX[x][L] for x in rk[:10])
expect(s, t, {'world': usd(W[L]), 'share': p1(EXPA['WLD'][L]), 's1970': p1(EXPA['WLD'][1970]), 'top10': p1(top10 / W[L] * 100), 'CHN': usd(EX['CHN'][L]), 'USA': usd(EX['USA'][L]), 'DEU': usd(EX['DEU'][L]),
              'IND': usd(EX['IND'][L]), 'VNM': usd(EX['VNM'][L]), 'LUX%': p1(EXP['LUX'][L]), 'HKG%': p1(EXP['HKG'][L]), 'SGP%': p1(EXP['SGP'][L]), 'USA%': p1(EXP['USA'][L]),
              'BGD': usd(EX['BGD'][L]), 'BGD2022': usd(EX['BGD'][2022]), 'BGD%': p1(EXP['BGD'][L]), 'BGD imp': usd(IM['BGD'][L]), 'BGD rank': ordn(rk.index('BGD') + 1), 'IND rank': ordn(rk.index('IND') + 1), 'VNM rank': ordn(rk.index('VNM') + 1)})
claim('exports: CHN USA DEU; LUX HKG SGP by share; BGD in bottom 15 by share', rk[:3] == ['CHN', 'USA', 'DEU'] and sk[:3] == ['LUX', 'HKG', 'SGP'] and sk.index('BGD') + 1 > len(sk) - 15)
claim('exports: world total is a gap-filled total in the metadata', 'Gap-filled total' in open('data/raw/wdi/NE.EXP.GNFS.CD.metadata.json').read())

# ---------- Imports ----------
s = 'imports-by-country'; p, t = page(s); L = 2024; rk = order(IM, L)
bal = sorted(((x, EX[x][L] - IM[x][L]) for x in rk if L in EX.get(x, {})), key=lambda z: -z[1])
expect(s, t, {'world': usd(IMA['WLD'][L]), 'share': p1(IMPA['WLD'][L]), 'USA': usd(IM['USA'][L]), 'CHN': usd(IM['CHN'][L]), 'DEU': usd(IM['DEU'][L]), 'IND': usd(IM['IND'][L]),
              'US deficit': usd(bal[-1][1]), 'IND deficit': usd(bal[-2][1]), 'PHL deficit': usd(bal[-3][1]), 'CHN surplus': usd(bal[0][1]), 'BGD': usd(IM['BGD'][L]), 'BGD%': p1(IMP['BGD'][L]),
              'BGD gap': usd(EX['BGD'][L] - IM['BGD'][L]), 'BGD rank': ordn(rk.index('BGD') + 1), 'IND rank': ordn(rk.index('IND') + 1), 'deficits': f'{sum(1 for _, b in bal if b < 0)} of the {len(bal)} economies'})
claim('imports: USA CHN DEU; balances US/IND/PHL deficits, CHN/IRL/SGP/DEU surpluses', rk[:3] == ['USA', 'CHN', 'DEU'] and [x for x, _ in bal[-3:]] == ['PHL', 'IND', 'USA'] and [x for x, _ in bal[:4]] == ['CHN', 'IRL', 'SGP', 'DEU'])
claim('imports: world 2020 dip and 2022 rise', IMA['WLD'][2020] < IMA['WLD'][2019] and IMA['WLD'][2022] > IMA['WLD'][2021])
cells = re.findall(r'<tr[^>]*data-iso3="(\w+)"[^>]*>.*?</tr>', p, re.S)
claim('imports: balance cells = exports minus imports', all((('+' if (EX[x][L] - IM[x][L]) > 0 else '') + bnc(EX[x][L] - IM[x][L])) in html.unescape(m) for x, m in zip(rk, re.findall(r'<tr[^>]*data-iso3="\w+"[^>]*>(.*?)</tr>', p, re.S))))

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
