# Run after `npm run build`: python3 scripts/verify/econ-batch17.py
# Independent check of the economy pages for Niger, Chad, Burundi, Haiti and Tajikistan (task 139):
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

usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion" if v >= 1e9 else f"${v/1e6:.1f} million" if v >= 1e6 else f"${round(v):,}"
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
EMP, _ = wdi('SL.AGR.EMPL.ZS'); LF, _ = wdi('SL.TLF.CACT.FE.ZS'); LM, _ = wdi('SL.TLF.CACT.MA.ZS')
lowpos = lambda S, c, y=L: len(ordr(S, y)) - ordr(S, y).index(c)
fall = [k for k in ordr(INF, L) if INF[k][L] < 0]

# ---------- Niger ----------
s, c = 'niger', 'NER'; t = common(s, c, None)
u5y = max(U5[c])
expect(t, s, {'defl': p1(abs(INF[c][L])), 'i2024': p1(INF[c][2024]), 'grank': ordn(rank(GR, c)), 'pclow': ordn(lowpos(PC, c)), 'g2022': p1(GR[c][2022]), 'g2021': p1(GR[c][2021]),
              'lit': p1(LIT[c][2022]), 'u5': f"{U5[c][u5y]:.1f}", 'agri': f"{round(EMP[c][L])}%"})
claim(s, 'prices fell, 2nd steepest of 12 after LKA; record GDP and per head; 17th; 7th lowest per head; record 1978; literacy 2022 2nd lowest; u5 2nd highest; remittances peak 2022, data to 2024',
      len(fall) == 12 and fall[-1] == 'LKA' and fall[-2] == c and peak(G, c) == L and peak(PC, c) == L and rank(GR, c) == 17 and lowpos(PC, c) == 7 and peak(GR, c) == 1978
      and [y for k, y, _ in lit if k == c] == [2022] and litlow(c) == 2 and ordr(U5, u5y)[:2] == ['NGA', c] and peak(REM, c) == 2022 and max(REM[c]) == 2024)

# ---------- Chad ----------
s, c = 'chad', 'TCD'; t = common(s, c, None)
ny = max(NET[c])
expect(t, s, {'defl': p1(abs(INF[c][L])), 'i2023': p1(INF[c][2023]), 'g2004': p1(GR[c][2004]), 'g1979': p1(abs(GR[c][1979])), 'lit': p1(LIT[c][2019]), 'netlow': ordn(lowpos(NET, c, ny)),
              'pcpeak': whole(PC[c][2012]), 'g2024': p1(GR[c][2024]), 'i2024': p1(INF[c][2024]), 'rem1994': whole(REM[c][1994]), 'remp1994': p1(REMP[c][1994]), 'x': f"{round(G[c][L] / G[c][2000])}"})
claim(s, 'record GDP; fastest since 2018; 15x 2000; peak 2004, worst 1979; prices fell 3rd steepest; lowest literacy (2019); internet 3rd lowest; per head below 2012; falls 2016/17/20; remittances end 1994',
      peak(G, c) == L and hi_since(GR, c) == 2018 and round(G[c][L] / G[c][2000]) == 15 and peak(GR, c) == 2004 and peak_low(GR, c) == 1979 and fall[-3] == c
      and lit[-1][0] == c and lit[-1][1] == 2019 and lowpos(NET, c, ny) == 3 and peak(PC, c) == 2012 and all(GR[c][y] < 0 for y in (2016, 2017, 2020)) and max(REM[c]) == 1994)

# ---------- Burundi ----------
s, c = 'burundi', 'BDI'; t = common(s, c, None)
ny = max(NET[c])
expect(t, s, {'irank': 'third' if rank(INF, c) == 3 else '?', 'iran-tur': 'Iran and Türkiye' if ordr(INF, L)[:2] in (['IRN','TUR'],['TUR','IRN']) else '?', 'agri': p1(EMP[c][L]), 'lfpF': p1(LF[c][L]), 'lfpM': p1(LM[c][L]), 'gdppeak2': 'only two', 'i': 'Iran and Türkiye', 'rem%': p1(REMP[c][L]), 'remrank': ordn(REMP_rank(c)), 'gdppeak': usd(G[c][2022])})
claim(s, 'lowest per head, also PPP; inflation 3rd, highest since 1979, >18% 2022-25; dollar GDP below 2022 peak; lowest internet; highest farm share; women > men; record remittances, 24th; growth best since 2019',
      ordr(PC, L)[-1] == c and ordr(PPP, L)[-1] == c and rank(INF, c) == 3 and hi_since(INF, c) == 1979 and all(INF[c][y] > 18 for y in range(2022, L + 1)) and peak(G, c) == 2022
      and ordr(NET, ny)[-1] == c and ordr(EMP, L)[0] == c and sorted(k for k in LF if k in econ and L in LF[k] and L in LM.get(k, {}) and LF[k][L] > LM[k][L]) == ['BDI', 'MDA'] and len(ordr(PC, L)) == 186 and len(ordr(NET, ny)) == 182 and peak(REM, c) == L and REMP_rank(c) == 24 and hi_since(GR, c) == 2019)

# ---------- Haiti ----------
s, c = 'haiti', 'HTI'
t = common(s, c, None)
remrank24 = [k for k, _ in sorted(((k, v[2024]) for k, v in REMP.items() if k in econ and 2024 in v), key=lambda x: (-x[1], x[0]))].index(c) + 1
expect(t, s, {'urank': ordn(rank(UN, c)), 'jump': f"{round((G[c][L] / G[c][L - 1] - 1) * 100)}%", 'rem%': p1(REMP[c][2024]), 'remrank': ordn(remrank24), 'g2024': p1(abs(GR[c][2024])), 'ppppeak': intd(PPP[c][2017]), 'i1994': p1(INF[c][1994])})
claim(s, 'falls every year 2019-25, growth in 2018; 3rd weakest; record dollar GDP; PPP below 2017 peak; inflation 4th, >15% since 2019, peak 1994; unemployment 16th; remittances 2024, 16th',
      all(GR[c][y] < 0 for y in range(2019, L + 1)) and GR[c][2018] > 0 and lowpos(GR, c) == 3 and peak(G, c) == L and peak(PPP, c) == 2017 and PPP[c][L] < PPP[c][2017]
      and rank(INF, c) == 4 and all(INF[c][y] > 15 for y in range(2019, L + 1)) and peak(INF, c) == 1994 and min(range(2019, L + 1), key=lambda y: GR[c][y]) == 2024 and len(ordr(INF, L)) == 169 and len(ordr(GR, L)) == 186 and rank(UN, c) == 16 and max(REM[c]) == 2024 and remrank24 == 16)

# ---------- Tajikistan ----------
s, c = 'tajikistan', 'TJK'; t = common(s, c, None)
ro = ordr(REMP, L)
expect(t, s, {'rem%': p1(REMP[c][L]), 'ton': p1(REMP[ro[1]][L]), 'up': f"{round((REM[c][L] / REM[c][L - 1] - 1) * 100)}%", 'x2015': f"{REM[c][L] / REM[c][2015]:.1f}", 'grank': ordn(rank(GR, c)),
              'avg': p1(avg_since(c)), 'g1992': p1(abs(GR[c][1992])), 'gx': f"{round(G[c][L] / G[c][2000])}"})
claim(s, 'record remittances and share; highest share, Tonga 2nd <40%; 7th fastest; 4th average since 2000 after GUY ETH CHN; 8%+ 2021-25; record GDP ~21x 2000; series start 1990/1986; worst 1992; no fall after 1996; inflation low 2025, series from 2001, peak 2001',
      peak(REM, c) == L and peak(REMP, c) == L and ro[0] == c and ro[1] == 'TON' and REMP['TON'][L] < 40 and rank(GR, c) == 7 and [k for k, _ in full_avg[:4]] == ['GUY', 'ETH', 'CHN', c]
      and all(GR[c][y] >= 8 for y in range(2021, L + 1)) and peak(G, c) == L and round(G[c][L] / G[c][2000]) == 21 and min(G[c]) == 1990 and min(GR[c]) == 1986 and peak_low(GR, c) == 1992
      and all(GR[c][y] < 0 for y in range(1989, 1997)) and max(neg(c)) == 1996 and peak_low(INF, c) == L and min(INF[c]) == 2001 and peak(INF, c) == 2001)

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
