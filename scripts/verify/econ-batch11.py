# Run after `npm run build`: python3 scripts/verify/econ-batch11.py
# Independent check of the economy pages for Morocco, Ghana, Kazakhstan, Chile and Angola (task 133):
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

# ---------- Morocco ----------
s, c = 'morocco', 'MAR'; t = common(s, c, None)
expect(t, s, {'rem': usd(REM[c][L]), 'rem%': p1(REMP[c][L]), 'times 2015': f"{REM[c][L] / REM[c][2015]:.1f}", 'times 2000': f"{G[c][L] / G[c][2000]:.1f}-fold",
              'infl2022': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]), 'infl2024': p1(INF[c][2024]), 'infl max': p1(INF[c][1974]), 'u1995': p1(UN[c][1995]),
              'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'more than': f"only {rank(REM, c) - 1} countries"})
claim(s, 'record GDP and per person; 9th in MENA; 57th', peak(G, c) == L and peak(PC, c) == L and order(G, L, MENA).index(c) == 8 and rank(G, c) == 57)
claim(s, 'growth fastest since 2021; inflation lowest since 2019; 2022 highest since 1991; peak 1974', above_since(GR, c, L) == 2021 and below_since(INF, c, L) == 2019 and above_since(INF, c, 2022) == 1991 and peak(INF, c) == 1974)
claim(s, '2020 deepest fall; unemployment peak 1995', peak_low(GR, c) == 2020 and peak(UN, c) == 1995)
claim(s, 'record remittances, dip 2016 then nine rises; 16th', peak(REM, c) == L and REM[c][2016] < REM[c][2015] and all(REM[c][y] > REM[c][y - 1] for y in range(2017, L + 1)) and rank(REM, c) == 16)

# ---------- Ghana ----------
s, c = 'ghana', 'GHA'; t = common(s, c, None)
expect(t, s, {'jump': f"{round((G[c][L] / G[c][L - 1] - 1) * 100)}%", 'times 2000': f"about {round(G[c][L] / G[c][2000])} times", 'best': p1(GR[c][2011]),
              'infl2023': p1(INF[c][2023]), 'infl2024': p1(INF[c][2024]), 'infl1983': p1(INF[c][1983]), 'rem peak': usd(REM[c][2015]), 'infl start': str(min(INF[c]))})
claim(s, 'record GDP and per person; 6th in SSA between AGO and CIV; 69th', peak(G, c) == L and peak(PC, c) == L and order(G, L, SSA)[4:7] == ['AGO', 'GHA', 'CIV'] and rank(G, c) == 69)
claim(s, 'growth fastest since 2019; best 2011', above_since(GR, c, L) == 2019 and peak(GR, c) == 2011)
claim(s, 'inflation lowest since 2021; 2023 highest since 2001; peak 1983', below_since(INF, c, L) == 2021 and above_since(INF, c, 2023) == 2001 and peak(INF, c) == 1983)
claim(s, 'remittances peak 2015, now under half', peak(REM, c) == 2015 and REM[c][L] < REM[c][2015] / 2)
claim(s, 'World Bank note: alternative conversion factor 1974-1987', '1974-1987' in econ[c]['SpecialNotes'])

# ---------- Kazakhstan ----------
s, c = 'kazakhstan', 'KAZ'; t = common(s, c, None)
expect(t, s, {'uzb x': f"{G[c][L] / G['UZB'][L]:.1f}", 'g2024': p1(GR[c][2024]), 'g1994': p1(abs(GR[c][1994])), 'g2001': p1(GR[c][2001]), 'infl1994': p1(INF[c][1994]),
              'infl2024': p1(INF[c][2024]), 'infl2022': p1(INF[c][2022]), 'pc x': f"about {round(PC[c][L] / PC[c][2000])} times", 'pc rank': ordn(rank(PC, c)), 'start': str(min(G[c]))})
claim(s, 'record GDP and per person; 48th/68th', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 48 and rank(PC, c) == 68)
claim(s, 'largest in Central Asia; >3x TKM+KGZ+TJK', all(G[c][L] > G[k][L] for k in ('UZB', 'TKM', 'KGZ', 'TJK')) and G[c][L] > 3 * sum(G[k][L] for k in ('TKM', 'KGZ', 'TJK')))
claim(s, 'growth fastest since 2011; shrank 1991-95, worst 1994; inflation series starts 1994 at its peak', above_since(GR, c, L) == 2011 and all(GR[c][y] < 0 for y in range(1991, 1996)) and peak_low(GR, c) == 1994 and min(INF[c]) == 1994 and peak(INF, c) == 1994 and INF[c][L] > INF[c][L - 1])

# ---------- Chile ----------
s, c = 'chile', 'CHL'; t = common(s, c, None)
expect(t, s, {'infl1974': p1(INF[c][1974]), 'infl2022': p1(INF[c][2022]), 'infl2023': p1(INF[c][2023]), 'g1975': p1(abs(GR[c][1975])), 'g1982': p1(abs(GR[c][1982])),
              'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'g1992': p1(GR[c][1992]), 'g1966 same': 'only 1966 and 1992, both at ' + p1(GR[c][1966]), 'g2024': p1(GR[c][2024]), 'u2024': p1(UN[c][2024]), 'u2009': p1(UN[c][2009]),
              'net rank': ordn(rank(NET, c, 2024)), 'pc rank': ordn(rank(PC, c))})
claim(s, 'record GDP and per person; 5th in LAC; 44th/62nd; high income', peak(G, c) == L and peak(PC, c) == L and order(G, L, LAC).index(c) == 4 and rank(G, c) == 44 and rank(PC, c) == 62 and econ[c]['IncomeGroup'] == 'High income')
claim(s, 'per head above BRA MEX ARG COL PER', all(PC[c][L] > PC[k][L] for k in ('BRA', 'MEX', 'ARG', 'COL', 'PER')))
claim(s, 'inflation peak 1974, series from 1971; 2022 highest since 1993', peak(INF, c) == 1974 and min(INF[c]) == 1971 and above_since(INF, c, 2022) == 1993)
claim(s, 'best growth 1992 then 2021; unemployment peak 2009, rising', peak(GR, c) == 1992 and sorted(GR[c], key=GR[c].get)[-3:] == [2021, 1966, 1992] and peak(UN, c) == 2009 and UN[c][L] > UN[c][L - 1])

# ---------- Angola ----------
s, c = 'angola', 'AGO'; t = common(s, c, None)
expect(t, s, {'peak': usd(G[c][2014]), 'below': f"{round((1 - G[c][L] / G[c][2014]) * 100)}%", 'pc peak': whole(PC[c][2012]), 'g2024': p1(GR[c][2024]), 'g2020': p1(abs(GR[c][2020])),
              'g1993': p1(abs(GR[c][1993])), 'g1995': p1(GR[c][1995]), 'infl2024': p1(INF[c][2024]), 'infl2023': p1(INF[c][2023]), 'infl1996': p1(INF[c][1996]), 'start': '1980'})
claim(s, 'GDP peak 2014, per head 2012; 5th in SSA between ETH and GHA; 68th', peak(G, c) == 2014 and peak(PC, c) == 2012 and order(G, L, SSA)[3:6] == ['ETH', 'AGO', 'GHA'] and rank(G, c) == 68 and min(G[c]) == 1980)
claim(s, 'shrank 2016-2020 only; worst 1993, best 1995', all(GR[c][y] < 0 for y in range(2016, 2021)) and GR[c][2015] > 0 and GR[c][2021] > 0 and peak_low(GR, c) == 1993 and peak(GR, c) == 1995)
claim(s, 'inflation >20% every year since 2020 except 2023; peak 1996', all(INF[c][y] > 20 for y in (2020, 2021, 2022, 2024, L)) and INF[c][2023] < 20 and peak(INF, c) == 1996)
uS = order(UN, L, SSA); claim(s, 'unemployment 9th highest of 45 SSA', uS.index(c) == 8 and len(uS) == 45)
claim(s, 'World Bank note: alternative conversion factor 1994-2025', '1994-2025' in econ[c]['SpecialNotes'])

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
