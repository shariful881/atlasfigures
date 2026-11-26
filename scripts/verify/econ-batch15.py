# Run after `npm run build`: python3 scripts/verify/econ-batch15.py
# Independent check of the economy pages for Senegal, Zambia, Rwanda, Honduras and Togo (task 137):
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



MENA = lambda k: econ[k]['Region'] == 'Middle East & North Africa'
SSA = lambda k: econ[k]['Region'] == 'Sub-Saharan Africa'
peak_low = lambda S, c: min(S[c], key=S[c].get)

REMP_rank = lambda c: [k for k, _ in sorted(((k, v[L]) for k, v in REMP.items() if k in econ and L in v), key=lambda x: (-x[1], x[0]))].index(c) + 1
avg_since = lambda c, y0=2000: sum(GR[c][y] for y in GR[c] if y >= y0) / len([y for y in GR[c] if y >= y0])
FA, _ = wdi('AG.LND.FRST.K2'); FP, _ = wdi('AG.LND.FRST.ZS'); EXP, _ = wdi('NE.EXP.GNFS.CD'); U5, _ = wdi('SH.DYN.MORT')
ordr = lambda S, y, keep=lambda k: True: [k for k, _ in sorted([(k, v[y]) for k, v in S.items() if k in econ and y in v and keep(k)], key=lambda x: (-x[1], x[0]))]
full_avg = sorted([(k, avg_since(k)) for k in GR if k in econ and L in GR[k] and all(y in GR[k] for y in range(2000, L + 1))], key=lambda z: -z[1])

# ---------- Senegal ----------
s, c = 'senegal', 'SEN'; t = common(s, c, None)
expect(t, s, {'g2020': p1(GR[c][2020]), 'i2022': p1(INF[c][2022]), 'i1994': p1(INF[c][1994]), 'u2015': p1(UN[c][2015]), 'rem': usd(REM[c][2023]), 'rem%': p1(REMP[c][2023]),
              'remrank': ordn(ordr(REMP, 2023).index(c) + 1), 'jump': 'about 15%', 'ssa': '14th'})
claim(s, 'record GDP/per head; 107th; 14th SSA; fastest since 2017; 7th SSA growth', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 107 and ordr(G, L, SSA).index(c) == 13 and max(y for y in GR[c] if y < L and GR[c][y] >= GR[c][L]) == 2017 and ordr(GR, L, SSA).index(c) == 6)
claim(s, 'dollar GDP +15%; last fall 1994; inflation peak 1994; unemployment lowest since 2005; remittances end 2023 at record', round((G[c][L] / G[c][L - 1] - 1) * 100) == 15 and neg(c)[-1] == 1994 and peak(INF, c) == 1994 and max(y for y in UN[c] if y < L and UN[c][y] <= UN[c][L]) == 2005 and max(REM[c]) == 2023 and peak(REM, c) == 2023)

# ---------- Zambia ----------
s, c = 'zambia', 'ZMB'; t = common(s, c, None)
netN = len(ordr(NET, 2024))
expect(t, s, {'peak': usd(G[c][2022]), 'pcpeak': whole(PC[c][2013]), 'i2024': p1(INF[c][2024]), 'i2019': p1(INF[c][2019]), 'i1993': p1(INF[c][1993]), 'irank': ordn(rank(INF, c)), 'avg': p1(avg_since(c)),
              'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'netlow': ordn(netN - ordr(NET, 2024).index(c)), 'netN': str(netN), 'rem%': p1(REMP[c][L]), 'forest': p1(FP[c][2024])})
claim(s, 'GDP below 2022 peak; per head peak 2013; inflation >10% 2020-25, <10% 2019; 12th; peak 1993', peak(G, c) == 2022 and G[c][L] < G[c][2022] and peak(PC, c) == 2013 and all(INF[c][y] > 10 for y in range(2020, L + 1)) and INF[c][2019] < 10 and rank(INF, c) == 12 and peak(INF, c) == 1993 and INF[c][L] < INF[c][2024])
claim(s, 'only fall since 1998 is 2020; growth same rounded as 2024; record remittances; 7th lowest internet', [y for y in neg(c) if y > 1998] == [2020] and f"{GR[c][L]:.1f}" == f"{GR[c][2024]:.1f}" and peak(REM, c) == L and netN - ordr(NET, 2024).index(c) == 7)

# ---------- Rwanda ----------
s, c = 'rwanda', 'RWA'; t = common(s, c, None)
pos = [k for k, _ in full_avg].index(c) + 1
expect(t, s, {'grank': ordn(rank(GR, c)), 'avg': p1(avg_since(c)), 'avgpos': ordn(pos), 'n': str(len(full_avg)), 'g1994': p1(abs(GR[c][1994])), 'g1995': p1(GR[c][1995]), 'pppx': f"{PPP[c][L] / PPP[c][2000]:.1f}-fold",
              'i2022': p1(INF[c][2022]), 'i2023': p1(INF[c][2023]), 'i2024': p1(INF[c][2024]), 'urank': ordn(rank(UN, c)), 'u2021': p1(UN[c][2021]), 'u5_2000': f"{U5[c][2000]:.1f}", 'u5_2024': f"{U5[c][2024]:.1f}", 'f1990': p1(FP[c][1990]), 'f2024': p1(FP[c][2024])})
claim(s, 'record GDP; low income; 6th growth, 2nd SSA after ETH; >7% 2021-25; 1994 worst; avg 6th after GUY ETH CHN TJK TKM', peak(G, c) == L and econ[c]['IncomeGroup'] == 'Low income' and rank(GR, c) == 6 and ordr(GR, L, SSA)[:2] == ['ETH', 'RWA'] and all(GR[c][y] > 7 for y in range(2021, L + 1)) and peak_low(GR, c) == 1994 and [k for k, _ in full_avg[:6]] == ['GUY', 'ETH', 'CHN', 'TJK', 'TKM', 'RWA'])

# ---------- Honduras ----------
s, c = 'honduras', 'HND'; t = common(s, c, None)
lacl = sorted([(k, 1 - FA[k][2023] / FA[k][1990]) for k in FA if k in econ and LAC(k) and FA[k].get(1990) and 2023 in FA[k]], key=lambda z: -z[1])
expect(t, s, {'rem%': p1(REMP[c][L]), 'remrank': ordn(ordr(REMP, L).index(c) + 1), 'up': f"{round((REM[c][L] / REM[c][2024] - 1) * 100)}%", 'vsexp': f"{round(REM[c][L] / EXP[c][L] * 100)}%", 'lac': ordn(ordr(G, L, LAC).index(c) + 1),
              'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'u2020': p1(UN[c][2020]), 'i2022': p1(INF[c][2022]), 'i1991': p1(INF[c][1991]), 'floss': f"{round((1 - FA[c][2023] / FA[c][1990]) * 100)}%", 'fpos': ordn([k for k, _ in lacl].index(c) + 1), 'f2023': p1(FP[c][2023])})
claim(s, 'record remittances & share; 4th after TJK TON NPL; record GDP; 104th; 2020 worst; unemp peak 2020; inflation peak 1991; forest loss order NIC PRY GTM HND', peak(REM, c) == L and peak(REMP, c) == L and ordr(REMP, L)[:4] == ['TJK', 'TON', 'NPL', 'HND'] and peak(G, c) == L and rank(G, c) == 104 and peak_low(GR, c) == 2020 and peak(UN, c) == 2020 and peak(INF, c) == 1991 and [k for k, _ in lacl[:4]] == ['NIC', 'PRY', 'GTM', 'HND'])

# ---------- Togo ----------
s, c = 'togo', 'TGO'; t = common(s, c, None)
uN = len(ordr(UN, L))
expect(t, s, {'grank': ordn(rank(GR, c)), 'x2015': f"{G[c][L] / G[c][2015]:.1f}", 'i2022': p1(INF[c][2022]), 'g1993': p1(abs(GR[c][1993])), 'i1994': p1(INF[c][1994]), 'ulow': ordn(uN - ordr(UN, L).index(c)), 'uN': str(uN),
              'u1993': p1(UN[c][1993]), 'rem': usd(REM[c][2020]), 'rem%': p1(REMP[c][2020])})
claim(s, 'record GDP/per head; 146th; >5% 2021-25, 2020 below; inflation lowest since 2017 (deflation); peaks', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 146 and all(GR[c][y] > 5 for y in range(2021, L + 1)) and GR[c][2020] < 5 and max(y for y in INF[c] if y < L and INF[c][y] <= INF[c][L]) == 2017 and INF[c][2017] < 0 and peak_low(GR, c) == 1993 and peak(INF, c) == 1994 and peak(UN, c) == 1993 and max(REM[c]) == 2020)

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
