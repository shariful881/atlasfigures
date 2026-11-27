# Run after `npm run build`: python3 scripts/verify/econ-batch19.py
# Independent check of the economy pages for Ireland, Austria, Czechia, Greece and Laos (task 141):
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
EMP, _ = wdi('SL.AGR.EMPL.ZS'); LF, _ = wdi('SL.TLF.CACT.FE.ZS'); LM, _ = wdi('SL.TLF.CACT.MA.ZS')
lowpos = lambda S, c, y=L: len(ordr(S, y)) - ordr(S, y).index(c)
fall = [k for k in ordr(INF, L) if INF[k][L] < 0]

MP, _ = wdi('SM.POP.TOTL.ZS')
gapsL = sorted([(k, LM[k][L] - LF[k][L]) for k in LM if k in econ and L in LM[k] and L in LF.get(k, {})], key=lambda x: -x[1])

MP, _ = wdi('SM.POP.TOTL.ZS')
gapsL = sorted([(k, LM[k][L] - LF[k][L]) for k in LM if k in econ and L in LM[k] and L in LF.get(k, {})], key=lambda x: -x[1])


# ---------- Ireland ----------
s, c = 'ireland', 'IRL'; t = common(s, c, None)
expect(t, s, {'pcrank': ordn(ordr(PC, L).index(c) + 1), 'grank': ordn(rank(GR, c)), 'gmax': p1(GR[c][2015]), 'g2016': p1(GR[c][2016]), 'g2021': p1(GR[c][2021]), 'g2023': p1(abs(GR[c][2023])), 'g2024': p1(GR[c][2024]),
              'exp': usd(EXP[c][L]), 'exp%': f"{round(EXP[c][L] / G[c][L] * 100)}%", 'exprank': ordn(ordr(EXP, L).index(c) + 1), 'x2000': f"{G[c][L] / G[c][2000]:.1f} times", 'umax': p1(UN[c][1991]), 'u2012': p1(UN[c][2012]),
              'i2022': p1(INF[c][2022]), 'imax': p1(INF[c][1975]), 'ppp': intd(PPP[c][L])})
claim(s, 'records; 2nd after LUX; 3rd growth, best since 2021; record 2015; fall 2023; exports 7th; unemployment peak 1991; inflation peak 1975',
      peak(G, c) == L and peak(PC, c) == L and ordr(PC, L)[:2] == ['LUX', c] and rank(GR, c) == 3 and hi_since(GR, c) == 2021 and peak(GR, c) == 2015 and GR[c][2023] < 0
      and ordr(EXP, L).index(c) == 6 and peak(UN, c) == 1991 and peak(INF, c) == 1975)

# ---------- Austria ----------
s, c = 'austria', 'AUT'; t = common(s, c, None)
b2b = [y for y in GR[c] if GR[c][y] < 0 and GR[c].get(y - 1, 1) < 0]
expect(t, s, {'g2023': p1(abs(GR[c][2023])), 'g2024': p1(abs(GR[c][2024])), 'glow': ordn(lowpos(GR, c)), 'i2022': p1(INF[c][2022]), 'i2024': p1(INF[c][2024]), 'umax': p1(UN[c][2021]), 'u2024': p1(UN[c][2024]),
              'pcrank': ordn(rank(PC, c)), 'forest': p1(FP[c][2024]), 'ppp': intd(PPP[c][L])})
claim(s, 'only back-to-back contraction 2023-24 since 1961; 20th weakest; records; 2022 inflation highest since 1974; unemployment peak 2021, rising',
      b2b == [2024] and min(GR[c]) == 1961 and lowpos(GR, c) == 20 and peak(G, c) == L and peak(PC, c) == L and max(k for k in INF[c] if k < 2022 and INF[c][k] >= INF[c][2022]) == 1974
      and peak(UN, c) == 2021 and UN[c][2024] < UN[c][L])

# ---------- Czechia ----------
s, c = 'czechia', 'CZE'; t = common(s, c, None)
expect(t, s, {'i2022': p1(INF[c][2022]), 'imax': p1(INF[c][1993]), 'i2023': p1(INF[c][2023]), 'i2024': p1(INF[c][2024]), 'ulow': ordn(lowpos(UN, c)), 'umin': p1(UN[c][2019]), 'umax': p1(UN[c][2000]),
              'u5': f"{U5[c][2024]:.1f}", 'u5low': ordn(lowpos(U5, c, 2024)), 'x2000': f"{G[c][L] / G[c][2000]:.1f} times", 'gdp2000': usd(G[c][2000]), 'g2024': p1(GR[c][2024]), 'worst': p1(GR[c][1991]), 'ppp': intd(PPP[c][L])})
claim(s, 'records; 2022 inflation highest since 1993 (series 1992, peak 1993); unemployment 34th lowest, low 2019, peak 2000; u5 13th lowest; best since 2022; flat 2023; worst 1991; GDP from 1990',
      peak(G, c) == L and peak(PC, c) == L and peak(PPP, c) == L and max(k for k in INF[c] if k < 2022 and INF[c][k] >= INF[c][2022]) == 1993 and min(INF[c]) == 1992 and peak(INF, c) == 1993
      and lowpos(UN, c) == 34 and peak_low(UN, c) == 2019 and peak(UN, c) == 2000 and lowpos(U5, c, 2024) == 13 and hi_since(GR, c) == 2022 and abs(GR[c][2023]) < 0.05 and peak_low(GR, c) == 1991 and min(G[c]) == 1990)

# ---------- Greece ----------
s, c = 'greece', 'GRC'; t = common(s, c, None)
expect(t, s, {'gdppeak': usd(G[c][2008]), 'gap': f"{round((1 - G[c][L] / G[c][2008]) * 100)}%", 'pcgap': f"{round((1 - PC[c][L] / PC[c][2008]) * 100)}%", 'pcpeak': whole(PC[c][2008]), 'worst': p1(GR[c][2011]),
              'g2020': p1(GR[c][2020]), 'g2021': p1(GR[c][2021]), 'umax': p1(UN[c][2013]), 'urank': ordn(rank(UN, c)), 'i2022': p1(INF[c][2022]), 'ilow': p1(INF[c][2015]), 'imax': p1(INF[c][1974]), 'ppp': intd(PPP[c][L])})
claim(s, 'dollar peaks 2008; PPP record; falls 2009-13 and 2015-16; worst 2011; 2.1% three years; unemployment peak 2013 above a quarter; deflation low 2015; peak 1974',
      peak(G, c) == 2008 and peak(PC, c) == 2008 and peak(PPP, c) == L and all(GR[c][y] < 0 for y in (2009, 2010, 2011, 2012, 2013, 2015, 2016)) and GR[c][2008] > 0 and peak_low(GR, c) == 2011
      and all(f'{GR[c][y]:.1f}' == '2.1' for y in (2023, 2024, 2025)) and peak(UN, c) == 2013 and UN[c][2013] > 25 and peak_low(INF, c) == 2015 and peak(INF, c) == 1974)

# ---------- Laos ----------
s, c = 'laos', 'LAO'; t = common(s, c, None)
expect(t, s, {'i2022': p1(INF[c][2022]), 'i2023': p1(INF[c][2023]), 'i2024': p1(INF[c][2024]), 'imax': p1(INF[c][1999]), 'irank': ordn(ordr(INF, 2023).index(c) + 1), 'g2020': p1(GR[c][2020]),
              'gdppeak': usd(G[c][2020]), 'agri': p1(EMP[c][L]), 'agrirank': ordn(ordr(EMP, L).index(c) + 1), 'lit': p1(LIT[c][2023]), 'rem': usd(REM[c][L]), 'rem%': p1(REMP[c][L]), 'ppp': intd(PPP[c][L])})
claim(s, 'GDP peak 2020, per head 2019; 2023 inflation highest since 1999 (peak), 10th; best since 2019; faster each year since 2020; agriculture 6th; literacy 2023; record remittances; GDP from 1984, inflation from 1989',
      peak(G, c) == 2020 and peak(PC, c) == 2019 and max(k for k in INF[c] if k < 2023 and INF[c][k] >= INF[c][2023]) == 1999 and peak(INF, c) == 1999 and ordr(INF, 2023).index(c) == 9
      and hi_since(GR, c) == 2019 and all(GR[c][y] > GR[c][y - 1] for y in range(2021, L + 1)) and ordr(EMP, L).index(c) == 5 and max(LIT[c]) == 2023 and peak(REM, c) == L and min(G[c]) == 1984 and min(INF[c]) == 1989)

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
