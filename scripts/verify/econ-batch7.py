# Run after `npm run build`: python3 scripts/verify/econ-batch7.py
# Independent check of the economy pages for South Africa, Kenya, Ethiopia, Argentina and Colombia (task 129):
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

# ---------- South Africa ----------
s, c = 'south-africa', 'ZAF'; t = common(s, c, None)
af = order(G, L, AFR); ud = order(UN, L); um, un_ = peak(UN, c), min(UN[c], key=UN[c].get)
expect(t, s, {'EGY': usd(G['EGY'][L]), 'NGA': usd(G['NGA'][L]), 'peak': usd(G[c][2011]), 'pc peak': whole(PC[c][2011]), 'SWZ': p1(UN['SWZ'][L]), 'u max': p1(UN[c][um]), 'u min': p1(UN[c][un_]),
              'g2020': p1(abs(GR[c][2020])), 'pc rank': ordn(rank(PC, c))})
claim(s, 'largest in Africa, EGY, NGA next', af[:3] == [c, 'EGY', 'NGA'])
claim(s, 'GDP and per person below 2011 peaks', peak(G, c) == 2011 and peak(PC, c) == 2011)
claim(s, 'second-highest unemployment after Eswatini; >30%', ud[:2] == ['SWZ', c] and UN[c][L] > 30)
claim(s, 'unemployment peak 2021, low 2007, from 1991', um == 2021 and un_ == 2007 and min(UN[c]) == 1991)
claim(s, 'growth <1% 2023-24; latest best since 2022; 2020 worst since 1961', GR[c][2023] < 1 and GR[c][2024] < 1 and above_since(GR, c, L) == 2022 and min(GR[c], key=GR[c].get) == 2020 and min(GR[c]) == 1961)
claim(s, 'inflation lowest since 2005', below_since(INF, c, L) == 2005)

# ---------- Kenya ----------
s, c = 'kenya', 'KEN'; t = common(s, c, None)
ssa = order(REM, L, lambda k: econ[k]['Region'] == 'Sub-Saharan Africa')
expect(t, s, {'ETH': usd(G['ETH'][L]), 'g2020': p1(abs(GR[c][2020])), 'rem %': p1(REMP[c][L]), 'rem rank': ordn(rank(REM, c)), 'pc rank': ordn(rank(PC, c))})
claim(s, 'record GDP and per person; sixth in Africa', peak(G, c) == L and peak(PC, c) == L and order(G, L, AFR).index(c) == 5)
claim(s, 'ahead of Ethiopia again after 2022-24', G[c][L] > G['ETH'][L] and all(G[c][y] < G['ETH'][y] for y in (2022, 2023, 2024)) and G[c][2021] > G['ETH'][2021])
claim(s, 'declines only 1961, 1970, 1992, 2020', neg(c) == [1961, 1970, 1992, 2020])
claim(s, 'inflation lowest since 2010', below_since(INF, c, L) == 2010)
claim(s, 'record remittances, >3x 2015, 2nd in SSA after NGA, 40th', peak(REM, c) == L and REM[c][L] > 3 * REM[c][2015] and ssa[:2] == ['NGA', c] and rank(REM, c) == 40)

# ---------- Ethiopia ----------
s, c = 'ethiopia', 'ETH'; t = common(s, c, None)
ry = max(REM[c]); im = peak(INF, c)
expect(t, s, {'peak 2024': usd(G[c][2024]), 'infl max': p1(INF[c][im]), 'rem rank': ordn(rank(REM, c, ry)), 'pc rank': ordn(rank(PC, c))})
claim(s, 'growth best since 2015; series from 1962; no decline since 2003', above_since(GR, c, L) == 2015 and min(GR[c]) == 1962 and neg(c)[-1] == 2003)
claim(s, 'dollar GDP peak 2024', peak(G, c) == 2024 and G[c][L] < G[c][2024])
claim(s, 'inflation lowest since 2017, >20% 2020-24, peak 2008', below_since(INF, c, L) == 2017 and all(INF[c][y] > 20 for y in range(2020, 2025)) and im == 2008)
claim(s, 'remittances latest 2024, 29th; 175th per person', ry == 2024 and rank(REM, c, ry) == 29 and rank(PC, c) == 175)

# ---------- Argentina ----------
s, c = 'argentina', 'ARG'; t = common(s, c, None)
lac = order(G, L, LAC)
expect(t, s, {'g2023': p1(abs(GR[c][2023])), 'g2024': p1(abs(GR[c][2024])), 'declines': f"{len(neg(c))} ", 'BRA pc': whole(PC['BRA'][L]), 'u 2002': p1(UN[c][2002]), 'pc rank': ordn(rank(PC, c))})
claim(s, 'record GDP and per person; 24th; third in LAC', peak(G, c) == L and peak(PC, c) == L and rank(G, c) == 24 and lac[:3] == ['BRA', 'MEX', c])
claim(s, 'growth after 2023-24 declines; best since 2022; 26 declines since 1961', GR[c][2023] < 0 and GR[c][2024] < 0 and above_since(GR, c, L) == 2022 and len(neg(c)) == 26)
claim(s, 'CPI only 2018-2024; 2024 highest in world', sorted(INF[c]) == list(range(2018, 2025)) and order(INF, 2024)[0] == c)
claim(s, 'unemployment peak 2002; richer than Brazil', peak(UN, c) == 2002 and PC[c][L] > PC['BRA'][L])

# ---------- Colombia ----------
s, c = 'colombia', 'COL'; t = common(s, c, None)
expect(t, s, {'g2020': p1(abs(GR[c][2020])), 'u 2000': p1(UN[c][2000]), 'infl 2023': p1(INF[c][2023]), 'rem %': p1(REMP[c][L]), 'rem rank': ordn(rank(REM, c)), 'times': f"{REM[c][L] / REM[c][2015]:.1f}-fold"})
claim(s, 'record GDP; 35th; fourth in LAC', peak(G, c) == L and rank(G, c) == 35 and order(G, L, LAC).index(c) == 3)
claim(s, 'declines only 1999 and 2020', neg(c) == [1999, 2020] and min(GR[c]) == 1961)
claim(s, 'unemployment lowest since 1994, peak 2000', below_since(UN, c, L) == 1994 and peak(UN, c) == 2000 and min(UN[c]) == 1991)
claim(s, '2023 inflation highest since 1998; latest lowest since 2021; growth best since 2022', above_since(INF, c, 2023) == 1998 and below_since(INF, c, L) == 2021 and above_since(GR, c, L) == 2022)
claim(s, 'record remittances, 17th', peak(REM, c) == L and rank(REM, c) == 17)

print(f'{ok} checks matched the original World Bank files.')
if bad:
    print('PROBLEMS:'); [print('  ✗', b) for b in bad]; sys.exit(1)
