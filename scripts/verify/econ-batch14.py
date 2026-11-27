# Run after `npm run build`: python3 scripts/verify/econ-batch14.py
# Independent check of the economy pages for Tunisia, Jordan, Bolivia, Dominican Republic and Portugal (task 136):
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
avg_since = lambda c, y0=2000: sum(GR[c][y] for y in GR[c] if y >= y0) / len([y for y in GR[c] if y >= y0])

# ---------- Tunisia ----------
s, c = 'tunisia', 'TUN'; t = common(s, c, None)
expect(t, s, {'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'avg': p1(avg_since(c)), 'u2011': p1(UN[c][2011]), 'u2007': p1(UN[c][2007]), 'urank': ordn(rank(UN, c)),
              'i2023': p1(INF[c][2023]), 'i2024': p1(INF[c][2024]), 'rem%': p1(REMP[c][L]), 'g2020': p1(abs(GR[c][2020])), 'g2011': f"{GR[c][2011]:.1f}%"})
claim(s, 'record GDP/per head; 92nd', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 92)
claim(s, 'unemployment >15% since 2015 (not 2014), >1/7, peak 2011, low 2007, 15th', all(UN[c][y] > 15 for y in UN[c] if y >= 2015) and UN[c][2014] < 15 and UN[c][L] > 100 / 7 and peak(UN, c) == 2011 and peak_low(UN, c) == 2007 and rank(UN, c) == 15)
claim(s, 'inflation peak 2023 in data from 1984; lowest since 2016; record remittances and share; ~2x 2015', peak(INF, c) == 2023 and min(INF[c]) == 1984 and below_since(INF, c, L) == 2016 and peak(REM, c) == L and peak(REMP, c) == L and round(REM[c][L] / REM[c][2015], 1) == 2.0)

# ---------- Jordan ----------
s, c = 'jordan', 'JOR'; t = common(s, c, None)
expect(t, s, {'urank': ordn(rank(UN, c)), 'u2021': p1(UN[c][2021]), 'u1991': p1(UN[c][1991]), 'i1989': p1(INF[c][1989]), 'g1989': p1(abs(GR[c][1989])), 'rem': usd(REM[c][2024]), 'rem%': p1(REMP[c][2024]),
              'peak': usd(REM[c][2014]), 'net rank': ordn(rank(NET, c, 2024)), 'start': '1965'})
claim(s, 'record GDP/per head; 89th; UMIC; growth 2.5-4% 2021-25', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 89 and econ[c]['IncomeGroup'] == 'Upper middle income' and all(2.5 < GR[c][y] < 4 for y in range(2021, L + 1)))
claim(s, 'unemployment 12th, lowest since 2016, about 1 in 6; peak 1991', rank(UN, c) == 12 and below_since(UN, c, L) == 2016 and 16 < UN[c][L] < 17.5 and peak(UN, c) == 1991)
claim(s, 'deflation 2015-16; 1989 worst growth and inflation peak; remittances end 2024, peak 2014', INF[c][2015] < 0 and INF[c][2016] < 0 and peak_low(GR, c) == 1989 and peak(INF, c) == 1989 and max(REM[c]) == 2024 and peak(REM, c) == 2014 and min(G[c]) == 1965)

# ---------- Bolivia ----------
s, c = 'bolivia', 'BOL'; t = common(s, c, None)
inf_order = order(INF, L)
expect(t, s, {'g2024': f"{GR[c][2024]:.1f}%", 'g2020': f"{GR[c][2020]:.1f}%", 'g2021': f"+{GR[c][2021]:.1f}%", 'i2023': p1(INF[c][2023]), 'i2024': p1(INF[c][2024]), 'i1985': p1(INF[c][1985]),
              'jump': f"{round((G[c][L] / G[c][L - 1] - 1) * 100)}%", 'more': f"Only {inf_order.index(c)} economies", 'irank': f"{ordn(inf_order.index(c) + 1)} of {len(inf_order)}"})
claim(s, 'negative years exactly 1980, 1982-86, 2020, 2024, 2025', [y for y in sorted(GR[c]) if GR[c][y] < 0] == [1980, 1982, 1983, 1984, 1985, 1986, 2020, 2024, 2025])
claim(s, 'inflation highest since 1991; peak 1985; >1000% 1984; dollar GDP record', above_since(INF, c, L) == 1991 and peak(INF, c) == 1985 and INF[c][1984] > 1000 and peak(G, c) == L and peak_low(GR, c) == 2020 and peak(GR, c) == 2021)

# ---------- Dominican Republic ----------
s, c = 'dominican-republic', 'DOM'; t = common(s, c, None)
lac_avg = sorted([(k, avg_since(k)) for k in GR if k in econ and LAC(k) and all(y in GR[k] for y in range(2000, L + 1))], key=lambda z: -z[1])
expect(t, s, {'avg': p1(avg_since(c)), 'pcx': f"{PC[c][L] / PC[c][2000]:.1f} times", 'g2024': p1(GR[c][2024]), 'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]),
              'rem%': p1(REMP[c][L]), 'remx': f"{REM[c][L] / REM[c][2015]:.1f}-fold", 'rem rank': ordn(rank(REM, c)), 'i2022': p1(INF[c][2022]), 'i2004': p1(INF[c][2004])})
claim(s, 'record GDP/per head; 9th LAC; 65th; third-fastest LAC average after GUY, PAN', peak(G, c) == L and peak(PC, c) == L and order(G, L, LAC).index(c) == 8 and rank(G, c) == 65 and [k for k, _ in lac_avg[:3]] == ['GUY', 'PAN', 'DOM'])
claim(s, 'slowest since 2020; record remittances; inflation peak 2004; unemployment lowest since 2008', below_since(GR, c, L) == 2020 and peak(REM, c) == L and peak(INF, c) == 2004 and below_since(UN, c, L) == 2008)

# ---------- Portugal ----------
s, c = 'portugal', 'PRT'; t = common(s, c, None)
expect(t, s, {'g2022': p1(GR[c][2022]), 'avg': p1(avg_since(c)), 'esp': whole(PC['ESP'][L]), 'u2013': p1(UN[c][2013]), 'i2022': p1(INF[c][2022]), 'i2023': p1(INF[c][2023]), 'i1977': p1(INF[c][1977]), 'g2020': f"{GR[c][2020]:.1f}%"})
claim(s, 'record GDP/per head; 45th/41st; below Spain', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 45 and rank(PC, c) == 41 and PC[c][L] < PC['ESP'][L])
claim(s, 'slower each year 2023-25, weakest since 2020; contraction 2011-13; unemployment peak 2013; worst 2020', all(GR[c][y] < GR[c][y - 1] for y in (2023, 2024, L)) and below_since(GR, c, L) == 2020 and all(GR[c][y] < 0 for y in (2011, 2012, 2013)) and peak(UN, c) == 2013 and peak_low(GR, c) == 2020)
claim(s, 'inflation lowest since 2021; 2022 highest since 1992; peak 1977; remittances up every year 2021-25, ~5x 2015', below_since(INF, c, L) == 2021 and above_since(INF, c, 2022) == 1992 and peak(INF, c) == 1977 and all(REM[c][y] > REM[c][y - 1] for y in range(2021, L + 1)) and round(REM[c][L] / REM[c][2015]) == 5)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
