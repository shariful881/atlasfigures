# Run after `npm run build`: python3 scripts/verify/econ-batch12.py
# Independent check of the economy pages for Uzbekistan, Mozambique, Madagascar, Côte d'Ivoire and Cameroon (task 134):
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

# ---------- Morocco ----------
s, c = 'morocco', 'MAR'; t = common(s, c, None)

# ---------- Uzbekistan ----------
s, c = 'uzbekistan', 'UZB'; t = common(s, c, None)
expect(t, s, {'jump': f"{round((G[c][L] / G[c][L - 1] - 1) * 100)}%", 'rem': usd(REM[c][L]), 'rem%': p1(REMP[c][L]), 'rem x': f"{REM[c][L] / REM[c][2015]:.1f}-fold",
              'infl2024': p1(INF[c][2024]), 'infl2018': p1(INF[c][2018]), 'g2024': p1(GR[c][2024]), 'g1992': f"{GR[c][1992]:.1f}%", 'x2000': f"roughly {round(G[c][L] / G[c][2000])} times", 'rem rank': ordn(rank(REM, c))})
claim(s, 'record GDP/per head; 60th; second in Central Asia; under half of KAZ', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 60 and sorted(['KAZ', 'UZB', 'TKM', 'KGZ', 'TJK'], key=lambda k: -G[k][L])[:2] == ['KAZ', 'UZB'] and G[c][L] < G['KAZ'][L] / 2)
claim(s, 'growth fastest since 2021, >6% since 2021; inflation lowest since 2016, series from 2011, peak 2018', above_since(GR, c, L) == 2021 and all(GR[c][y] > 6 for y in range(2021, L + 1)) and below_since(INF, c, L) == 2016 and min(INF[c]) == 2011 and peak(INF, c) == 2018)
claim(s, 'record remittances, 12th, over a seventh of GDP; worst 1992; GDP from 1987; shrank 1991-95', peak(REM, c) == L and rank(REM, c) == 12 and REMP[c][L] > 100 / 7 and peak_low(GR, c) == 1992 and min(G[c]) == 1987 and all(GR[c][y] < 0 for y in range(1991, 1996)))

# ---------- Mozambique ----------
s, c = 'mozambique', 'MOZ'; t = common(s, c, None)
expect(t, s, {'peak24': usd(G[c][2024]), 'pc2014': whole(PC[c][2014]), 'infl2016': p1(INF[c][2016]), 'infl2022': p1(INF[c][2022]), 'best': p1(GR[c][1987]),
              'pc rank': f"{ordn(rank(PC, c))} of {len([k for k in PC if k in econ and L in PC[k]])}", 'starts': 'remittances from 1980'})
claim(s, 'shrank 2025, only 2020 since 1993; grew 1993-2019', GR[c][L] < 0 and [y for y in GR[c] if 1993 <= y < L and GR[c][y] < 0] == [2020] and min(GR[c]) == 1981)
claim(s, 'GDP peak 2024, per head 2014; low income; 4th lowest per head; best 1987; inflation 2005, peak 2016', peak(G, c) == 2024 and peak(PC, c) == 2014 and econ[c]['IncomeGroup'] == 'Low income' and rank(PC, c) == len([k for k in PC if k in econ and L in PC[k]]) - 3 and peak(GR, c) == 1987 and min(INF[c]) == 2005 and peak(INF, c) == 2016 and min(G[c]) == 1991 and min(REM[c]) == 1980)

# ---------- Madagascar ----------
s, c = 'madagascar', 'MDG'; t = common(s, c, None)
nN = len([k for k in NET if k in econ and 2024 in NET[k]])
expect(t, s, {'g2024': p1(GR[c][2024]), 'g2002': p1(abs(GR[c][2002])), 'g2009': p1(abs(GR[c][2009])), 'g2020': p1(abs(GR[c][2020])), 'infl1995': p1(INF[c][1995]), 'infl2024': p1(INF[c][2024]),
              'rem jump': f"{round((REM[c][L] / REM[c][L - 1] - 1) * 100)}%", 'rem': usd(REM[c][L]), 'net': f"{ordn(rank(NET, c, 2024))} of {nN}", 'x2000': f"{G[c][L] / G[c][2000]:.1f} times"})
claim(s, 'record GDP and per head; third-lowest per head; low income', peak(G, c) == L and peak(PC, c) == L and rank(PC, c) == len([k for k in PC if k in econ and L in PC[k]]) - 2 and econ[c]['IncomeGroup'] == 'Low income')
claim(s, 'slowest growth since 2020; 3-5% since 2021; worst 2002; inflation peak 1995; record remittances', below_since(GR, c, L) == 2020 and all(3 <= GR[c][y] < 5 for y in range(2021, L + 1)) and peak_low(GR, c) == 2002 and peak(INF, c) == 1995 and peak(REM, c) == L)

# ---------- Côte d'Ivoire ----------
s, c = 'cote-divoire', 'CIV'; t = common(s, c, None)
expect(t, s, {'g2011': p1(abs(GR[c][2011])), 'g1980': p1(abs(GR[c][1980])), 'infl2022': p1(INF[c][2022]), 'infl2024': p1(INF[c][2024]), 'rem': usd(REM[c][2024]),
              'rem x': f"roughly {round(REM[c][2024] / REM[c][2020])}-fold", 'x2000': f"roughly {round(G[c][L] / G[c][2000])}-fold", 'gs': ', '.join(p1(GR[c][y]) for y in range(2021, 2025))})
claim(s, 'record GDP under 100bn; 7th SSA after Ghana; 76th', peak(G, c) == L and peak(PC, c) == L and 99.5e9 < G[c][L] < 1e11 and order(G, L, SSA)[5:7] == ['GHA', 'CIV'] and rank(G, c) == 76)
claim(s, '>=6% growth 2021-25; last contraction 2011; worst 1980; inflation lowest since 1990 (negative)', all(GR[c][y] >= 6 for y in range(2021, L + 1)) and max(y for y in GR[c] if GR[c][y] < 0) == 2011 and peak_low(GR, c) == 1980 and below_since(INF, c, L) == 1990 and INF[c][1990] < 0)
claim(s, 'remittances end 2024 at record', max(REM[c]) == 2024 and peak(REM, c) == 2024)

# ---------- Cameroon ----------
s, c = 'cameroon', 'CMR'; t = common(s, c, None)
expect(t, s, {'g1988': p1(abs(GR[c][1988])), 'g1993': p1(abs(GR[c][1993])), 'infl1994': p1(INF[c][1994]), 'infl2023': p1(INF[c][2023]), 'infl2024': p1(INF[c][2024]),
              'band': f"between {p1(min(GR[c][y] for y in range(2021, L + 1)))} and {p1(max(GR[c][y] for y in range(2021, L + 1)))}", 'rem': usd(REM[c][2024]), 'x2000': f"{G[c][L] / G[c][2000]:.1f} times"})
claim(s, 'record GDP and per head; 12th SSA; 91st; lower middle income', peak(G, c) == L and peak(PC, c) == L and order(G, L, SSA).index(c) == 11 and rank(G, c) == 91 and econ[c]['IncomeGroup'] == 'Lower middle income')
claim(s, 'contracted 1987-93 only those 7 in a row; recovery 1994; inflation peak 1994, 2023 highest since 1995, now lowest since 2021', all(GR[c][y] < 0 for y in range(1987, 1994)) and GR[c][1986] > 0 and GR[c][1994] > 0 and peak(INF, c) == 1994 and above_since(INF, c, 2023) == 1995 and below_since(INF, c, L) == 2021)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
