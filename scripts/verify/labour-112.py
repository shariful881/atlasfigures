# Run after `npm run build`: python3 scripts/verify/labour-112.py
# Independent check of the female labour force participation and employment-in-agriculture ranking pages (task 112): reads the ORIGINAL World Bank zips
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
FF, econ = wdi('SL.TLF.CACT.FE.ZS'); MM, _ = wdi('SL.TLF.CACT.MA.ZS'); AG, _ = wdi('SL.AGR.EMPL.ZS'); IN, _ = wdi('SL.IND.EMPL.ZS'); SV, _ = wdi('SL.SRV.EMPL.ZS')
FFA = wdi_agg('SL.TLF.CACT.FE.ZS'); MMA = wdi_agg('SL.TLF.CACT.MA.ZS'); AGA = wdi_agg('SL.AGR.EMPL.ZS'); INA = wdi_agg('SL.IND.EMPL.ZS'); SVA = wdi_agg('SL.SRV.EMPL.ZS')
for x in ('SL.TLF.CACT.FE.ZS', 'SL.TLF.CACT.MA.ZS', 'SL.AGR.EMPL.ZS', 'SL.IND.EMPL.ZS', 'SL.SRV.EMPL.ZS'):
    claim(f'{x}: licence CC BY-4.0', '"CC BY-4.0"' in open(f'data/raw/wdi/{x}.metadata.json').read())
f1 = lambda v: f'{v:.1f}%'  # same as JavaScript toFixed(1) on the same double
L = 2025; B = 1991
for s, S, col in (('female-labor-force-participation-by-country', FF, 'labour_force_participation_women_pct_15_plus'), ('employment-in-agriculture-by-country', AG, 'employment_agriculture_pct')):
    p, t = page(s); rk = order(S, L); rows = rows_of(p)
    claim(f'{s}: year {L} = latest world', max((FFA if S is FF else AGA)['WLD']) == L)
    claim(f'{s}: rows = original ({len(rk)})', len(rows) == len(rk) and [(r[0], r[1]) for r in rows] == [(x, i + 1) for i, x in enumerate(rk)] and all(r[2] == f1(S[r[0]][L]) for r in rows))
    c = csv_rows(s); h = c[0]
    claim(f'{s}: CSV = original', len(c) - 1 == len(rk) and all(r[2] == rk[i] and float(r[h.index(col)]) == S[rk[i]][L] for i, r in enumerate(c[1:])))

# ---------- Women in the labour force ----------
s = 'female-labor-force-participation-by-country'; p, t = page(s); rk = order(FF, L); W = FFA['WLD']
trs = re.findall(r'<tr[^>]*data-iso3="(\w+)"[^>]*>(.*?)</tr>', p, re.S)
claim('lfp: men and gap cells', all([x.strip() for x in re.findall(r'<td[^>]*>([^<]*)</td>', m)][-2:] == [f1(MM[k][L]), f'{MM[k][L] - FF[k][L]:.1f}'] for k, m in trs))
u20 = [k for k in rk if FF[k][L] < 20]
expect(s, t, {'world': f1(W[L]), 'men': f1(MMA['WLD'][L]), '1991': f1(W[B]), 'min': f1(min(W.values())), 'MDG': f1(FF['MDG'][L]), 'SLB': f1(FF['SLB'][L]), 'NGA': f1(FF['NGA'][L]), 'YEM': f1(FF['YEM'][L]), 'AFG': f1(FF['AFG'][L]), 'IRQ': f1(FF['IRQ'][L]),
              'MENA': f1(FFA['MEA'][L]), 'SSA': f1(FFA['SSF'][L]), 'BGD': f1(FF['BGD'][L]), 'BGD1991': f1(FF['BGD'][B]), 'BGDm': f1(MM['BGD'][L]), 'BGD rank': ordn(rk.index('BGD') + 1), 'IND': f1(FF['IND'][L]), 'PAK': f1(FF['PAK'][L]),
              'SAU': f1(FF['SAU'][L]), 'SAUx': f'{FF["SAU"][L] / FF["SAU"][B]:.1f}-fold', 'BDI': f1(FF['BDI'][L]), 'BDIm': f1(MM['BDI'][L]), 'MDA': f1(FF['MDA'][L]), 'MDAm': f1(MM['MDA'][L]), 'gap': f'{MMA["WLD"][L] - W[L]:.1f} points', 'u20': f'{len(u20)} countries'})
claim('lfp: order; lowest; under 20 all MENA region; women ahead only BDI MDA; world low 2020; weighted average', rk[:3] == ['MDG', 'SLB', 'NGA'] and rk[-3:] == ['IRQ', 'AFG', 'YEM'] and all(econ[k]['Region'].startswith('Middle East') for k in u20) and sorted(k for k in rk if MM[k][L] < FF[k][L]) == ['BDI', 'MDA'] and min(W, key=W.get) == 2020 and 'Weighted average' in open('data/raw/wdi/SL.TLF.CACT.FE.ZS.metadata.json').read())

# ---------- Agriculture ----------
s = 'employment-in-agriculture-by-country'; p, t = page(s); rk = order(AG, L); W = AGA['WLD']; WS = SVA['WLD']
cross = max(y for y in W if W[y] >= WS[y]) + 1
drops = sorted(rk, key=lambda k: AG[k][L] - AG[k][B])
expect(s, t, {'world': f1(W[L]), '1991': f1(W[B]), 'srv': f1(WS[L]), 'srv1991': f1(WS[B]), 'ind': f1(INA['WLD'][L]), 'cross': f'since {cross}', 'BDI': f1(AG['BDI'][L]), 'MOZ': f1(AG['MOZ'][L]), 'SGP': f1(AG['SGP'][L]), 'HKG': f1(AG['HKG'][L]), 'MAC': f1(AG['MAC'][L]),
              'over50': f'In {sum(1 for k in rk if AG[k][L] > 50)} countries', 'SSA': f1(AGA['SSF'][L]), 'LIC': f1(AGA['LIC'][L]), 'HIC': f1(AGA['HIC'][L]), 'CHN1991': f1(AG['CHN'][B]), 'CHN': f1(AG['CHN'][L]), 'USA': f1(AG['USA'][L]),
              'BGD': f1(AG['BGD'][L]), 'BGD1991': f1(AG['BGD'][B]), 'BGDs': f1(SV['BGD'][L]), 'BGDi': f1(IN['BGD'][L]), 'BGD rank': ordn(rk.index('BGD') + 1), 'IND': f1(AG['IND'][L]), 'PAK': f1(AG['PAK'][L]), 'VNM': f'{abs(AG["VNM"][L] - AG["VNM"][B]):.1f} percentage points'})
claim('agri: order; lowest SGP HKG MAC; services ahead since 2001 and >50% in 2025; industry 20-25%; biggest drops VNM RWA KHM', rk[:3] == ['BDI', 'MOZ', 'NER'] and rk[-3:] == ['MAC', 'HKG', 'SGP'] and cross == 2001 and WS[L] > 50 and all(20 < v < 25 for v in INA['WLD'].values()) and drops[:3] == ['VNM', 'RWA', 'KHM'])
trs = re.findall(r'<tr[^>]*data-iso3="(\w+)"[^>]*>(.*?)</tr>', p, re.S)
claim('agri: industry and services cells', all(f1(IN[k][L]) in html.unescape(m) and f1(SV[k][L]) in html.unescape(m) for k, m in trs))

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
