# Run after `npm run build`: python3 scripts/verify/econ-batch13.py
# Independent check of the economy pages for Romania, Ecuador, Guatemala, Cambodia and Belgium (task 135):
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
REMP_rank = lambda c: [k for k, _ in sorted(((k, v[L]) for k, v in REMP.items() if k in econ and L in v), key=lambda x: (-x[1], x[0]))].index(c) + 1

# ---------- Romania ----------
s, c = 'romania', 'ROU'; t = common(s, c, None)
expect(t, s, {'gs': ', '.join(p1(GR[c][y]) for y in (2022, 2023, 2024)), 'g2021': p1(GR[c][2021]), 'infl2022': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]), 'infl2024': p1(INF[c][2024]),
              'infl1993': p1(INF[c][1993]), 'g1991': p1(abs(GR[c][1991])), 'x2000': f"around {round(G[c][L] / G[c][2000])} times", 'rem rank': ordn(rank(REM, c)), 'pc rank': ordn(rank(PC, c))})
claim(s, 'record GDP/per head; 37th; high income; > Czechia, < half Poland', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 37 and econ[c]['IncomeGroup'] == 'High income' and G['CZE'][L] < G[c][L] < G['POL'][L] / 2)
claim(s, 'growth slower each year 2022-25; weakest since 2020; inflation up; 2022 highest since 2003; peak 1993', all(GR[c][y] < GR[c][y - 1] for y in range(2022, L + 1)) and below_since(GR, c, L) == 2020 and INF[c][L] > INF[c][L - 1] and above_since(INF, c, 2022) == 2003 and peak(INF, c) == 1993)
claim(s, 'unemployment highest since 2015; record remittances 2x 2015; GDP from 1987, worst 1991', above_since(UN, c, L) == 2015 and peak(REM, c) == L and round(REM[c][L] / REM[c][2015], 1) == 2.0 and min(G[c]) == 1987 and peak_low(GR, c) == 1991 and '1987-1992' in econ[c]['SpecialNotes'])

# ---------- Ecuador ----------
s, c = 'ecuador', 'ECU'; t = common(s, c, None)
expect(t, s, {'g2024': p1(abs(GR[c][2024])), 'infl2000': p1(INF[c][2000]), 'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'i2018': f"{INF[c][2018]:.1f}%", 'i2020': f"{INF[c][2020]:.1f}%",
              'rem x': f"{REM[c][L] / REM[c][2015]:.1f} times", 'rem rank': ordn(rank(REM, c)), 'more': f"{rank(REM, c) - 1} countries"})
claim(s, 'record GDP/per head; 7th LAC; 63rd; UMIC', peak(G, c) == L and peak(PC, c) == L and order(G, L, LAC).index(c) == 6 and rank(G, c) == 63 and econ[c]['IncomeGroup'] == 'Upper middle income')
claim(s, 'shrank 2024, grew 2025; worst 2020; inflation lowest since 2021; negative only 2018, 2020; peak 2000', GR[c][L - 1] < 0 < GR[c][L] and peak_low(GR, c) == 2020 and below_since(INF, c, L) == 2021 and [y for y in INF[c] if INF[c][y] < 0] == [2018, 2020] and peak(INF, c) == 2000)
claim(s, 'record remittances; unemployment lowest since 2013', peak(REM, c) == L and below_since(UN, c, L) == 2013)

# ---------- Guatemala ----------
s, c = 'guatemala', 'GTM'; t = common(s, c, None)
expect(t, s, {'rem%': p1(REMP[c][L]), 'rem2015': usd(REM[c][2015]), 'g2024': p1(GR[c][2024]), 'infl2022': p1(INF[c][2022]), 'infl1990': p1(INF[c][1990]), 'rem rank': ordn(rank(REM, c)), 'pc rank': ordn(rank(PC, c)), 'share rank': f"Only {REMP_rank(c) - 1} economies"})
claim(s, 'record GDP/per head; 10th LAC; 67th', peak(G, c) == L and peak(PC, c) == L and order(G, L, LAC).index(c) == 9 and rank(G, c) == 67)
claim(s, 'record remittances and share; >1/5; LAC second after Mexico; 9th; about 4x 2015', peak(REM, c) == L and peak(REMP, c) == L and REMP[c][L] > 20 and order(REM, L, LAC)[:2] == ['MEX', 'GTM'] and rank(REM, c) == 9 and round(REM[c][L] / REM[c][2015]) == 4)
claim(s, 'growth fastest since 2021; inflation lowest since 1982; peak 1990; only 1982, 83, 85, 2020 negative', above_since(GR, c, L) == 2021 and below_since(INF, c, L) == 1982 and peak(INF, c) == 1990 and [y for y in sorted(GR[c]) if GR[c][y] < 0] == [1982, 1983, 1985, 2020] and '1985-2003' in econ[c]['SpecialNotes'])

# ---------- Cambodia ----------
s, c = 'cambodia', 'KHM'; t = common(s, c, None)
avg = sum(GR[c][y] for y in GR[c] if y >= 2000) / len([y for y in GR[c] if y >= 2000])
expect(t, s, {'avg': p1(avg), 'g2024': p1(GR[c][2024]), 'g2018': p1(GR[c][2018]), 'g2019': p1(GR[c][2019]), 'g2020': f"{GR[c][2020]:.1f}%", 'infl2008': p1(INF[c][2008]),
              'rem peak': usd(REM[c][2024]), 'drop': f"{round((1 - REM[c][L] / REM[c][2024]) * 100)}%", 'x2000': f"{round(G[c][L] / G[c][2000])} times"})
claim(s, 'record GDP > 50bn, first time; 94th', peak(G, c) == L and peak(PC, c) == L and G[c][L] > 5e10 and all(G[c][y] < 5e10 for y in G[c] if y < L) and rank(G, c) == 94)
claim(s, 'only 2020 negative since 1995; GDP from 1975; inflation from 1995, peak 2008', [y for y in GR[c] if y >= 1995 and GR[c][y] < 0] == [2020] and min(G[c]) == 1975 and min(INF[c]) == 1995 and peak(INF, c) == 2008 and '1963-2004' in econ[c]['SpecialNotes'])
claim(s, 'unemployment second-lowest after Qatar; remittances peaked 2024', order(UN, L)[-2:] == ['KHM', 'QAT'] and peak(REM, c) == 2024)

# ---------- Belgium ----------
s, c = 'belgium', 'BEL'; t = common(s, c, None)
expect(t, s, {'gs': ', '.join(p1(GR[c][y]) for y in (2022, 2023, 2024)), 'g2021': p1(GR[c][2021]), 'g2020': f"{GR[c][2020]:.1f}%", 'infl2022': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]),
              'infl1975': p1(INF[c][1975]), 'u1994': p1(UN[c][1994]), 'rem rank': ordn(rank(REM, c)), 'pc rank': ordn(rank(PC, c))})
claim(s, 'record GDP/per head; 22nd/15th; between half and all of Netherlands', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 22 and rank(PC, c) == 15 and G['NLD'][L] / 2 < G[c][L] < G['NLD'][L])
claim(s, 'slower each year 2022-25, weakest since 2020; inflation lowest since 2021, 2022 highest since 1975 peak; recessions 1975 81 93 2009 2020, worst 2020; unemployment peak 1994',
      all(GR[c][y] < GR[c][y - 1] for y in range(2022, L + 1)) and below_since(GR, c, L) == 2020 and below_since(INF, c, L) == 2021 and above_since(INF, c, 2022) == 1975 and peak(INF, c) == 1975
      and [y for y in sorted(GR[c]) if GR[c][y] < 0] == [1975, 1981, 1993, 2009, 2020] and peak_low(GR, c) == 2020 and peak(UN, c) == 1994 and rank(REM, c) == 14)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
