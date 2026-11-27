# Run after `npm run build`: python3 scripts/verify/econ-batch16.py
# Independent check of the economy pages for Guinea, Malawi, Mali, Benin and Burkina Faso (task 138):
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



MENA = lambda k: econ[k]['Region'] == 'Middle East & North Africa'
SSA = lambda k: econ[k]['Region'] == 'Sub-Saharan Africa'
peak_low = lambda S, c: min(S[c], key=S[c].get)

REMP_rank = lambda c: [k for k, _ in sorted(((k, v[L]) for k, v in REMP.items() if k in econ and L in v), key=lambda x: (-x[1], x[0]))].index(c) + 1
avg_since = lambda c, y0=2000: sum(GR[c][y] for y in GR[c] if y >= y0) / len([y for y in GR[c] if y >= y0])
FA, _ = wdi('AG.LND.FRST.K2'); FP, _ = wdi('AG.LND.FRST.ZS'); EXP, _ = wdi('NE.EXP.GNFS.CD'); U5, _ = wdi('SH.DYN.MORT')
ordr = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: (-x[1], x[0]))]
full_avg = sorted([(k, avg_since(k)) for k in GR if k in econ and L in GR[k] and all(y in GR[k] for y in range(2000, L + 1))], key=lambda z: -z[1])
LIT, _ = wdi('SE.ADT.LITR.ZS')
lit = sorted([(k, max(y for y in s if y >= 2015), s[max(y for y in s if y >= 2015)]) for k, s in LIT.items() if k in econ and any(y >= 2015 for y in s)], key=lambda z: (-z[2], z[0]))
litlow = lambda c: len(lit) - [k for k, _, _ in lit].index(c)
hi_since = lambda S, c, y=L: max(k for k in S[c] if k < y and S[c][k] >= S[c][y])

# ---------- Benin ----------
s, c = 'benin', 'BEN'; t = common(s, c, None)
uo = ordr(UN, L)
expect(t, s, {'g2024': p1(GR[c][2024]), 'avg': p1(avg_since(c)), 'i1994': p1(INF[c][1994]), 'ulow': ordn(len(uo) - uo.index(c)), 'grank': ordn(rank(GR, c)), 'rem': usd(REM[c][2023]), 'rem%': p1(REMP[c][2023])})
claim(s, 'record GDP; 122nd; fastest since 1990; 9th; 4th SSA after ETH RWA ZWE; no fall since 1989; >6% 2021-25; peak inflation 1994', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 122 and hi_since(GR, c) == 1990 and rank(GR, c) == 9 and ordr(GR, L, SSA)[:4] == ['ETH', 'RWA', 'ZWE', 'BEN'] and neg(c)[-1] == 1989 and all(GR[c][y] > 6 for y in range(2021, L + 1)) and peak(INF, c) == 1994 and max(REM[c]) == 2023)

# ---------- Guinea ----------
s, c = 'guinea', 'GIN'; t = common(s, c, None)
expect(t, s, {'g2016': p1(GR[c][2016]), 'grank': ordn(rank(GR, c)), 'i2024': p1(INF[c][2024]), 'i2006': p1(INF[c][2006]), 'lit': p1(LIT[c][2018]), 'litlow': ordn(litlow(c)), 'u5': f"{U5[c][2024]:.1f}", 'rem': usd(REM[c][2024])})
claim(s, 'record GDP; 116th; fastest since 2017; peak 2016; falls only 1977 1979 2009; lowest inflation since 2005 start; peak 2006; literacy 2018 5th lowest', peak(G, c) == L and rank(G, c) == 116 and hi_since(GR, c) == 2017 and peak(GR, c) == 2016 and neg(c) == [1977, 1979, 2009] and peak_low(INF, c) == L and min(INF[c]) == 2005 and peak(INF, c) == 2006 and [y for k, y, _ in lit if k == c] == [2018] and litlow(c) == 5 and min(G[c]) == 1970)

# ---------- Malawi ----------
s, c = 'malawi', 'MWI'; t = common(s, c, None)
po = ordr(PC, L); no = ordr(NET, 2024)
expect(t, s, {'irank': ordn(rank(INF, c)), 'i2024': p1(INF[c][2024]), 'i2023': p1(INF[c][2023]), 'i2021': p1(INF[c][2021]), 'i1995': p1(INF[c][1995]), 'pcpeak': whole(PC[c][2011]), 'drop': f"{round((1 - G[c][2024] / G[c][2023]) * 100)}%",
              'g2024': p1(GR[c][2024]), 'gdp2023': usd(G[c][2023]), 'gdp2024': usd(G[c][2024]), 'avg': p1(avg_since(c)), 'net': p1(NET[c][2024]), 'netN': str(len(no))})
claim(s, 'inflation 5th, >20% 2022-25; per head 6th lowest, below 2011; dollar GDP fell 2024, record 2025; growth <2% 2022-25; last fall 2001; internet 10th lowest; GDP from 1980, growth from 1961', rank(INF, c) == 5 and all(INF[c][y] > 20 for y in range(2022, L + 1)) and len(po) - po.index(c) == 6 and peak(PC, c) == 2011 and G[c][2024] < G[c][2023] and peak(G, c) == L and all(GR[c][y] < 2 for y in range(2022, L + 1)) and neg(c)[-1] == 2001 and len(no) - no.index(c) == 10 and min(G[c]) == 1980 and min(GR[c]) == 1961 and peak(INF, c) == 1995)

# ---------- Mali ----------
s, c = 'mali', 'MLI'; t = common(s, c, None)
expect(t, s, {'g2020': p1(abs(GR[c][2020])), 'g2001': p1(GR[c][2001]), 'lit': p1(LIT[c][2024]), 'i2022': p1(INF[c][2022]), 'rem': usd(REM[c][2024]), 'rem%': p1(REMP[c][2024]), 'forest': p1(FP[c][2024]), 'ssa': 'fifteenth'})
claim(s, 'record GDP; 113th; 15th SSA; fastest since 2016; faster each year 2021-25; peak 2001; literacy 2024 among 3 lowest; deflation 2013/16/19 since 2010; from 1967', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 113 and ordr(G, L, SSA).index(c) == 14 and hi_since(GR, c) == 2016 and all(GR[c][y] >= GR[c][y - 1] for y in range(2022, L + 1)) and GR[c][2020] < 0 and peak(GR, c) == 2001 and litlow(c) <= 3 and [y for y in sorted(INF[c]) if y >= 2010 and INF[c][y] < 0] == [2013, 2016, 2019] and min(G[c]) == 1967)

# ---------- Burkina Faso ----------
s, c = 'burkina-faso', 'BFA'; t = common(s, c, None)
fall = [k for k in ordr(INF, L) if INF[k][L] < 0]
expect(t, s, {'jump': f"{round((G[c][L] / G[c][L - 1] - 1) * 100)}%", 'defl': p1(abs(INF[c][L])), 'i2022': p1(INF[c][2022]), 'i1977': p1(INF[c][1977]), 'nfall': str(len(fall)), 'lit': p1(LIT[c][2023]), 'litlow': ordn(litlow(c)),
              'rem': usd(REM[c][2024]), 'rem%': p1(REMP[c][2024]), 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'pcx': f"{PC[c][L] / PC[c][2000]:.1f}-fold"})
claim(s, 'record GDP +19%; 118th; deflation, 5th steepest of 12; peak 1977; last fall 1990; record remittances 2024', peak(G, c) == L and rank(G, c) == 118 and len(fall) == 12 and fall[-5] == c and peak(INF, c) == 1977 and neg(c)[-1] == 1990 and peak(REM, c) == 2024 and max(REM[c]) == 2024)

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
