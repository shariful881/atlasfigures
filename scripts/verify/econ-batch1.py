# Run after `npm run build`: python3 scripts/verify/econ-batch1.py
# Independent check of the economy pages for the United States, India, China, the United Kingdom and Canada:
# reads the ORIGINAL World Bank zips (data/raw/wdi/) and the UN WPP file, never the site's generated data, and
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
    p = open(f'dist/country/{slug}/economy/index.html').read()
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
         'GDP rank': ordn(rank(G, c)), 'PPP': intd(PPP[c][L]), 'unemployment': p1(UN[c][L]), 'internet': p1(last(NET, c)[1]), 'remittances': usd(last(REM, c)[1])}
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

# ---------- United States ----------
s, c = 'united-states', 'USA'; t = common(s, c, None)
three = G['CHN'][L] + G['DEU'][L] + G['JPN'][L]
expect(t, s, {'gap with China': usd(G[c][L] - G['CHN'][L]), 'gap with three': usd(G[c][L] - three), 'pop share': p1(pop['USA'] / pop['WORLD'] * 100), 'pc rank': ordn(rank(PC, c)),
              'pc 1960': whole(PC[c][1960]), 'times 1960': f"roughly {round(PC[c][L] / PC[c][1960])} times", 'growth 2024': p1(GR[c][2024]), 'g2009': sp(GR[c][2009]), 'g2020': sp(GR[c][2020]), 'g2021': p1(GR[c][2021]),
              'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'infl 2024': p1(INF[c][2024]), 'unemp 2020': p1(UN[c][2020]), 'unemp 2010': p1(UN[c][2010])})
claim(s, 'bigger than China+Germany+Japan', G[c][L] > three)
claim(s, 'no 2025 CPI', L not in INF[c])
claim(s, 'only 2009, 2020 negative since 2000', [y for y in GR[c] if y > 2000 and GR[c][y] < 0] == [2009, 2020])
claim(s, '2021 fastest since 1984', [y for y in GR[c] if y > 1984 and GR[c][y] >= GR[c][2021]] == [2021] and GR[c][1984] > GR[c][2021])
claim(s, '2022 inflation highest since 1981', INF[c][1981] > INF[c][2022] and all(INF[c][y] < INF[c][2022] for y in INF[c] if y > 1981 and y != 2022))
claim(s, 'US lead over China wider than 2021', G['CHN'][L] / G[c][L] < G['CHN'][2021] / G[c][2021])

# ---------- India ----------
s, c = 'india', 'IND'; t = common(s, c, None)
top10 = sorted([(k, v[L]) for k, v in G.items() if k in econ and L in v], key=lambda x: -x[1])[:10]
expect(t, s, {'UK GDP': usd(G['GBR'][L]), 'growth 2024': p1(GR[c][2024]), 'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'pc rank': ordn(rank(PC, c)), 'BGD pc': whole(PC['BGD'][L]),
              'rem % GDP': p1(REMP[c][L]), 'rem 2021': usd(REM[c][2021]), 'infl 2024': p1(INF[c][2024]), 'net 2015': p1(NET[c][2015])})
claim(s, 'fastest of top 10', all(GR[k][L] < GR[c][L] for k, _ in top10 if k != c))
claim(s, 'ahead of UK only 2022–24', [y for y in G[c] if y in G['GBR'] and G[c][y] > G['GBR'][y]] == [2022, 2023, 2024])
claim(s, 'only 2020 negative since 1979', [y for y in GR[c] if y > 1979 and GR[c][y] < 0] == [2020])
claim(s, 'largest remittance receiver', rank(REM, c) == 1)
claim(s, 'inflation lowest since 1976', all(INF[c][y] > INF[c][L] for y in INF[c] if 1976 < y < L) and INF[c][1976] < INF[c][L])
claim(s, 'unemployment near series low', UN[c][L] - min(UN[c].values()) < 0.1)

# ---------- China ----------
s, c = 'china', 'CHN'; t = common(s, c, None)
expect(t, s, {'GDP 2000': usd(G[c][2000]), 'g2007': p1(GR[c][2007]), 'g2020': p1(GR[c][2020]), 'ratio 2021': p1(G[c][2021] / G['USA'][2021] * 100), 'ratio 2025': p1(G[c][L] / G['USA'][L] * 100),
              'infl 2024': p1(INF[c][2024]), 'infl 2023': p1(INF[c][2023]), 'world pc': whole(PC['WLD'][L]), 'share of US pc': f"about {round(PC[c][L] / PC['USA'][L] * 100)}%", 'pc 2000': whole(PC[c][2000])})
claim(s, 'almost 16-fold since 2000', 15 < G[c][L] / G[c][2000] < 16.5)
claim(s, 'no other $1T economy grew as much since 2000', all(G[k][L] / G[k][2000] < G[c][L] / G[c][2000] for k, v in G.items() if k in econ and k != c and v.get(L, 0) > 1e12 and 2000 in v))
claim(s, '2007 fastest since 1992', [y for y in GR[c] if y > 1992 and GR[c][y] >= GR[c][2007]] == [2007])
claim(s, 'no contraction since 1976', all(GR[c][y] >= 0 for y in GR[c] if y > 1976) and GR[c][1976] < 0)
claim(s, 'inflation under 0.3% 2023–25, lowest since 2009', all(0 <= INF[c][y] < 0.3 for y in (2023, 2024, L)) and all(INF[c][y] > INF[c][L] for y in INF[c] if 2009 < y < L) and INF[c][2009] < 0)
claim(s, 'pc just under world average', 0.95 < PC[c][L] / PC['WLD'][L] < 1)

# ---------- United Kingdom ----------
s, c = 'united-kingdom', 'GBR'; t = common(s, c, None)
back = next(y for y in sorted(PC[c]) if y > 2007 and PC[c][y] > PC[c][2007])
g7 = ['USA', 'GBR', 'DEU', 'JPN', 'FRA', 'ITA', 'CAN']
expect(t, s, {'India GDP': usd(G['IND'][L]), 'g2020': p1(abs(GR[c][2020])), 'g2009': p1(abs(GR[c][2009])), 'g2021': p1(GR[c][2021]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]),
              'pc 2007': whole(PC[c][2007]), 'back above': f"until {back}", 'pc rank': ordn(rank(PC, c)), 'infl 2022': p1(INF[c][2022]), 'infl 2023': p1(INF[c][2023]), 'unemp 2022': p1(UN[c][2022])})
claim(s, 'fifth, India ahead 2022–24', rank(G, c) == 5 and all(G['IND'][y] > G[c][y] for y in (2022, 2023, 2024)))
claim(s, '2020 deepest, 2021 strongest since 1961', min(GR[c], key=GR[c].get) == 2020 and max(GR[c], key=GR[c].get) == 2021 and min(GR[c]) == 1961)
claim(s, 'back above 2007 in 2024', back == 2024)
claim(s, '2022 inflation highest since 1990', INF[c][1990] > INF[c][2022] and all(INF[c][y] < INF[c][2022] for y in INF[c] if y > 1990 and y != 2022))
claim(s, 'highest G7 inflation with 2025 figure', all(INF[k][L] < INF[c][L] for k in g7 if k != c and L in INF[k]))

# ---------- Canada ----------
s, c = 'canada', 'CAN'; t = common(s, c, None)
peak = max((y for y in PC[c] if y < 2021), key=lambda y: PC[c][y]); regained = next(y for y in sorted(PC[c]) if y > peak and PC[c][y] > PC[c][peak]); low = min((y for y in PC[c] if peak < y < regained), key=lambda y: PC[c][y])
g7u = sorted(g7, key=lambda k: -UN[k][L])
expect(t, s, {'Brazil': usd(G['BRA'][L]), 'gap Brazil': usd(G[c][L] - G['BRA'][L]), 'US pc': whole(PC['USA'][L]), 'pct of US': f"about {round(PC[c][L] / PC['USA'][L] * 100)}%", 'US PPP': intd(PPP['USA'][L]),
              'peak': whole(PC[c][peak]), 'low': whole(PC[c][low]), 'regained': f"until {regained}", 'unemp 2022': p1(UN[c][2022]), 'France unemp': p1(UN['FRA'][L]), 'infl 2022': p1(INF[c][2022]), 'g2020': p1(abs(GR[c][2020]))})
claim(s, 'tenth, Brazil eleventh', rank(G, c) == 10 and rank(G, 'BRA') == 11)
claim(s, 'peak 2012, low 2016, regained 2021', (peak, low, regained) == (2012, 2016, 2021))
claim(s, 'G7 unemployment: France first, Canada second', g7u[:2] == ['FRA', 'CAN'])
claim(s, 'unemployment highest since 2021', all(UN[c][y] < UN[c][L] for y in (2022, 2023, 2024)) and UN[c][2021] > UN[c][L])
claim(s, 'inflation about a third of 2022', 0.28 < INF[c][L] / INF[c][2022] < 0.36)
claim(s, 'only 2020 negative since 2009', [y for y in GR[c] if y > 2009 and GR[c][y] < 0] == [2020])

print(f'{ok} checks matched the original World Bank / UN files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
