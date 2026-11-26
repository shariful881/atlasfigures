# Run after `npm run build`: python3 scripts/verify/econ-batch10.py
# Independent check of the economy pages for Norway, Poland, Ukraine, New Zealand and Peru (task 132):
# reads the ORIGINAL World Bank zips (data/raw/wdi/), never the site's generated data, and
# confirms every figure in the text, Key facts, tables and CSVs, plus the claims behind each sentence.
import csv, io, zipfile, gzip, re, html, sys, json

def wdi(code):
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        n = z.namelist()
        lines = z.read([x for x in n if x.startswith('API_')][0]).decode('utf-8-sig').splitlines()
        meta = list(csv.DictReader(io.StringIO(z.read([x for x in n if x.startswith('Metadata_Country')][0]).decode('utf-8-sig'))))
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    return ({r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)} for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))},
            {m['Country Code']: m for m in meta if m['Region']})

G, econ = wdi('NY.GDP.MKTP.CD'); PC, _ = wdi('NY.GDP.PCAP.CD'); PPP, _ = wdi('NY.GDP.PCAP.PP.CD'); GR, _ = wdi('NY.GDP.MKTP.KD.ZG')
INF, _ = wdi('FP.CPI.TOTL.ZG'); UN, _ = wdi('SL.UEM.TOTL.ZS'); REM, _ = wdi('BX.TRF.PWKR.CD.DT'); REMP, _ = wdi('BX.TRF.PWKR.DT.GD.ZS'); NET, _ = wdi('IT.NET.USER.ZS')
pop = {}
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz', 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['Variant'] == 'Medium' and r['Time'] == '2025' and (r['ISO3_code'] in ('USA',) or r['Location'] == 'World'):
            pop[r['ISO3_code'] or 'WORLD'] = float(r['TPopulation1July'])

usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion" if v >= 1e9 else f"${v/1e6:.1f} million"
whole = lambda v: f"${round(v):,}"
intd = lambda v: f"Int${round(v):,}"
p1 = lambda v: f"{v:.1f}%"
sp = lambda v: ('+' if round(v, 1) > 0 else '') + f"{v:.1f}%"
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"
L = 2025
rank = lambda src, c, y=L: [k for k, _ in sorted([(k, s[y]) for k, s in src.items() if k in econ and y in s], key=lambda x: -x[1])].index(c) + 1
last = lambda src, c: (max(src[c]), src[c][max(src[c])])
ok = 0; bad = []

def page(slug):
    p = open(f'dist/economy/{slug}/index.html').read()
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', p, flags=re.S))))
    return p, t
def expect(t, slug, d):
    global ok
    for k, v in d.items():
        if v in t: ok += 1
        else: bad.append(f'{slug}: {k} {v} not on the page')
def claim(slug, k, c):
    global ok
    if c: ok += 1
    else: bad.append(f'{slug}: claim false: {k}')
def common(slug, c, years):
    """Figures every page shows (Key facts, cards, table, CSV)."""
    global ok
    p, t = page(slug)
    iy, iv = last(INF, c)
    d = {'GDP': usd(G[c][L]), 'GDP per person': whole(PC[c][L]), 'growth': sp(GR[c][L]), 'inflation': p1(iv), 'share of world': p1(G[c][L] / G['WLD'][L] * 100),
         'GDP rank': ordn(rank(G, c)), 'PPP': intd(PPP[c][L]), 'unemployment': p1(UN[c][L]), 'internet': p1(last(NET, c)[1]), **({'remittances': usd(last(REM, c)[1])} if REM.get(c) else {})}
    expect(t, slug, d)
    for tr in re.findall(r'<tr[^>]*data-year="(\d{4})"[^>]*>(.*?)</tr>', p, re.S):
        y = int(tr[0]); cells = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>', tr[1], re.S)]
        want = [f"{G[c][y]/1e9:.1f}" if y in G[c] else '–', whole(PC[c][y]) if y in PC[c] else '–', sp(GR[c][y]) if y in GR[c] else '–', p1(INF[c][y]) if y in INF[c] else '–', p1(REMP[c][y]) if y in REMP[c] else '–']
        if cells == want: ok += 1
        else: bad.append(f'{slug} table {y}: {cells} ≠ {want}')
    rows = [l for l in open(f'dist/data/{slug}-economy.csv').read().splitlines() if l and not l.startswith('#')][1:]
    for l in rows:
        f = l.split(','); y = int(f[0])
        for i, src in enumerate([G, PC, PPP, GR, INF, UN, REM, REMP, NET]):
            w = src[c].get(y)
            if (w is None and f[i + 1] == '') or (w is not None and float(f[i + 1]) == w): ok += 1
            else: bad.append(f'{slug} CSV {y} col {i+1}')
    return t

neg = lambda c: [y for y in sorted(GR[c]) if GR[c][y] < 0]
below_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] < S[c][y])
above_since = lambda S, c, y: max(k for k in S[c] if k < y and S[c][k] > S[c][y])
order = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: -x[1])]
AFR = lambda k: econ[k]['Region'] == 'Sub-Saharan Africa' or k in ('DZA', 'EGY', 'LBY', 'MAR', 'TUN')
LAC = lambda k: econ[k]['Region'] == 'Latin America & Caribbean'
peak = lambda S, c: max(S[c], key=S[c].get)



def common_nou(slug, c):
    """common() for a page with no latest-year unemployment (Ukraine): skip that key, check the rest."""
    global ok
    p, t = page(slug)
    iy, iv = last(INF, c)
    d = {'GDP': usd(G[c][L]), 'GDP per person': whole(PC[c][L]), 'growth': sp(GR[c][L]), 'inflation': p1(iv), 'GDP rank': ordn(rank(G, c)), 'PPP': intd(PPP[c][L]),
         'unemployment (last)': p1(last(UN, c)[1]), 'internet': p1(last(NET, c)[1]), 'remittances': usd(last(REM, c)[1])}
    expect(t, slug, d)
    rows = [l for l in open(f'dist/data/{slug}-economy.csv').read().splitlines() if l and not l.startswith('#')][1:]
    for l in rows:
        f = l.split(','); y = int(f[0])
        for i, src in enumerate([G, PC, PPP, GR, INF, UN, REM, REMP, NET]):
            w = src.get(c, {}).get(y)
            if (w is None and f[i + 1] == '') or (w is not None and float(f[i + 1]) == w): ok += 1
            else: bad.append(f'{slug} CSV {y} col {i+1}')
    return t

# ---------- Norway ----------
s, c = 'norway', 'NOR'; t = common(s, c, None)
expect(t, s, {'peak': usd(G[c][2022]), 'drop': f"{round((1 - G[c][L] / G[c][2022]) * 100)}%", 'u2022': p1(UN[c][2022]), 'u2023': p1(UN[c][2023]), 'u2024': p1(UN[c][2024]), 'infl2022': p1(INF[c][2022])})
claim(s, 'sixth per person after LUX IRL CHE SGP ISL', order(PC, L)[:6] == ['LUX', 'IRL', 'CHE', 'SGP', 'ISL', c])
claim(s, 'GDP and per person peak 2022; three declines', peak(G, c) == 2022 and peak(PC, c) == 2022 and neg(c) == [1988, 2009, 2020])
claim(s, 'unemployment up 3 years, highest since 2016; inflation lowest since 2020', all(UN[c][y] > UN[c][y - 1] for y in (2023, 2024, L)) and above_since(UN, c, L) == 2016 and below_since(INF, c, L) == 2020)

# ---------- Poland ----------
s, c = 'poland', 'POL'; t = common(s, c, None)
expect(t, s, {'gdp2000': usd(G[c][2000]), 'pc2000': whole(PC[c][2000]), 'u2002': p1(UN[c][2002]), 'u2023': p1(UN[c][2023]), 'infl2022': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]), 'rem rank': ordn(rank(REM, c))})
claim(s, 'first year above $1tn; record per person; 21st; ~6x 2000', [y for y in G[c] if G[c][y] >= 1e12] == [L] and peak(PC, c) == L and rank(G, c) == 21 and round(G[c][L] / G[c][2000]) == 6)
claim(s, 'declines only 1991, 2020; growth best since 2022', neg(c) == [1991, 2020] and above_since(GR, c, L) == 2022)
claim(s, 'unemployment peak 2002, low 2023; CPI from 1971', peak(UN, c) == 2002 and min(UN[c], key=UN[c].get) == 2023 and min(INF[c]) == 1971)

# ---------- Ukraine ----------
s, c = 'ukraine', 'UKR'; t = common_nou(s, c)
expect(t, s, {'g2022': p1(abs(GR[c][2022])), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'gdp2021': usd(G[c][2021]), 'infl2024': p1(INF[c][2024]), 'infl2022': p1(INF[c][2022]), 'rem peak': usd(REM[c][2021])})
claim(s, '2022 worst since 1988; record dollar GDP; 56th', min(GR[c], key=GR[c].get) == 2022 and min(GR[c]) == 1988 and peak(G, c) == L and rank(G, c) == 56)
claim(s, 'growth since 2023 smaller than 2022 loss', (1 + GR[c][2023] / 100) * (1 + GR[c][2024] / 100) * (1 + GR[c][L] / 100) * (1 + GR[c][2022] / 100) < 1 and below_since(GR, c, L) == 2022)
claim(s, 'falls every year 1990-99; 1993 CPI peak >4000%; unemployment ends 2021', all(GR[c][y] < 0 for y in range(1990, 2000)) and peak(INF, c) == 1993 and INF[c][1993] > 4000 and max(UN[c]) == 2021)
claim(s, 'remittances peak 2021, 25th', peak(REM, c) == 2021 and rank(REM, c) == 25 and REM[c][L] < 0.6 * REM[c][2021])

# ---------- New Zealand ----------
s, c = 'new-zealand', 'NZL'; t = common(s, c, None)
expect(t, s, {'g2024': p1(abs(GR[c][2024])), 'u2022': p1(UN[c][2022]), 'pc2021': whole(PC[c][2021]), 'infl2022': p1(INF[c][2022]), 'pc rank': ordn(rank(PC, c))})
claim(s, '2024 contraction, <1% 2025; unemployment highest since 2016 from 2022 low', GR[c][2024] < 0 and 0 < GR[c][L] < 1 and above_since(UN, c, L) == 2016 and min(UN[c], key=UN[c].get) == 2022)
claim(s, 'record GDP, per person peak 2021; inflation lowest since 2020; remittances end 2022', peak(G, c) == L and peak(PC, c) == 2021 and below_since(INF, c, L) == 2020 and max(REM[c]) == 2022)

# ---------- Peru ----------
s, c = 'peru', 'PER'; t = common(s, c, None)
expect(t, s, {'g2020': sp(GR[c][2020]), 'g2021': sp(GR[c][2021]), 'infl2022': p1(INF[c][2022]), 'rem rank': ordn(rank(REM, c)), 'times': f"{REM[c][L] / REM[c][2015]:.1f}"})
claim(s, 'record GDP and per person; 6th in LAC; 46th', peak(G, c) == L and peak(PC, c) == L and order(G, L, LAC).index(c) == 5 and rank(G, c) == 46)
claim(s, '2021 best growth; hyperinflation 1989-90; inflation lowest since 2018', peak(GR, c) == 2021 and INF[c][1989] > 1000 and INF[c][1990] > 7000 and below_since(INF, c, L) == 2018)
claim(s, 'record remittances, 38th', peak(REM, c) == L and rank(REM, c) == 38)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
