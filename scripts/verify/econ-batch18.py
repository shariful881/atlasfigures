# Run after `npm run build`: python3 scripts/verify/econ-batch18.py
# Independent check of the economy pages for Papua New Guinea, Oman, Slovakia, Uruguay and Kyrgyzstan (task 140):
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

MP, _ = wdi('SM.POP.TOTL.ZS')
gapsL = sorted([(k, LM[k][L] - LF[k][L]) for k in LM if k in econ and L in LM[k] and L in LF.get(k, {})], key=lambda x: -x[1])

# ---------- Papua New Guinea ----------
s, c = 'papua-new-guinea', 'PNG'; t = common(s, c, None)
ny = max(NET[c])
expect(t, s, {'pcpeak': whole(PC[c][2022]), 'grank': ordn(rank(GR, c)), 'i2024': p1(INF[c][2024]), 'imax': p1(INF[c][1974]), 'forest': p1(FP[c][2024]), 'forestrank': ordn(ordr(FP, 2024).index(c) + 1),
              'netlow': ordn(lowpos(NET, c, ny)), 'men': p1(LM[c][L]), 'women': p1(LF[c][L]), 'menlow': ordn(lowpos(LM, c)), 'rem': usd(REM[c][2024])})
claim(s, 'record GDP and PPP; per head below 2022; fastest since 2022, 37th; falls 2018/20/21; inflation low 2024 since 1972, peak 1974; forest 10th; internet 9th lowest; men 8th lowest; rem ends 2024',
      peak(G, c) == L and peak(PPP, c) == L and peak(PC, c) == 2022 and hi_since(GR, c) == 2022 and rank(GR, c) == 37 and all(GR[c][y] < 0 for y in (2018, 2020, 2021)) and peak_low(INF, c) == 2024 and min(INF[c]) == 1972
      and peak(INF, c) == 1974 and ordr(FP, 2024).index(c) == 9 and lowpos(NET, c, ny) == 9 and lowpos(LM, c) == 8 and max(REM[c]) == 2024)

# ---------- Oman ----------
s, c = 'oman', 'OMN'; t = common(s, c, None)
expect(t, s, {'pcpeak': whole(PC[c][2008]), 'drop': f"{round((1 - PC[c][L] / PC[c][2008]) * 100)}%", 'gdppeak': usd(G[c][2022]), 'g2022': p1(GR[c][2022]), 'g2023': p1(GR[c][2023]), 'g2024': p1(GR[c][2024]), 'imax': p1(INF[c][2008]),
              'mig': p1(MP[c][2024]), 'mig2000': p1(MP[c][2000]), 'migrank': ordn(ordr(MP, 2024).index(c) + 1), 'men': p1(LM[c][L]), 'women': p1(LF[c][L]), 'menrank': ordn(ordr(LM, L).index(c) + 1)})
claim(s, 'per head peak 2008, 25% lower; GDP peak 2022; falls 2019/20; inflation <3% since 2012, peak 2008, from 2001; migrants 22nd; men 4th; gap 3rd after AFG IRQ',
      peak(PC, c) == 2008 and round((1 - PC[c][L] / PC[c][2008]) * 100) == 25 and peak(G, c) == 2022 and GR[c][2019] < 0 and GR[c][2020] < 0 and all(INF[c][y] < 3 for y in INF[c] if y >= 2012) and INF[c][2011] >= 3
      and peak(INF, c) == 2008 and min(INF[c]) == 2001 and ordr(MP, 2024).index(c) == 21 and ordr(LM, L).index(c) == 3 and [k for k, _ in gapsL[:3]] == ['AFG', 'IRQ', c])

# ---------- Slovakia ----------
s, c = 'slovakia', 'SVK'; t = common(s, c, None)
expect(t, s, {'g2022': p1(GR[c][2022]), 'g2024': p1(GR[c][2024]), 'glow': ordn(lowpos(GR, c)), 'umin': p1(UN[c][2024]), 'umax': p1(UN[c][2001]), 'i2022': p1(INF[c][2022]), 'i2023': p1(INF[c][2023]), 'i2024': p1(INF[c][2024]),
              'exp': usd(EXP[c][L]), 'exp%': f"{round(EXP[c][L] / G[c][L] * 100)}% of", 'rem%': p1(REMP[c][L]), 'worst': p1(abs(GR[c][1991])), 'ppp': intd(PPP[c][L])})
claim(s, 'records GDP/per head/PPP; weakest since 2022, 24th lowest; unemployment low 2024, peak 2001; 2022 inflation highest since 1994; record remittances; worst 1991; GDP from 1990',
      peak(G, c) == L and peak(PC, c) == L and peak(PPP, c) == L and max(k for k in GR[c] if k < L and GR[c][k] <= GR[c][L]) == 2022 and lowpos(GR, c) == 24 and peak_low(UN, c) == 2024 and peak(UN, c) == 2001
      and max(k for k in INF[c] if k < 2022 and INF[c][k] >= INF[c][2022]) == 1994 and peak(REM, c) == L and peak_low(GR, c) == 1991 and min(G[c]) == 1990)

# ---------- Uruguay ----------
s, c = 'uruguay', 'URY'; t = common(s, c, None)
expect(t, s, {'pcrank': ordn(rank(PC, c)), 'irank': ordn(rank(INF, c)), 'i2022': p1(INF[c][2022]), 'i2024': p1(INF[c][2024]), 'imax': p1(INF[c][1968]), 'g2002': p1(abs(GR[c][2002])), 'drop': f"{round((1 - G[c][2002] / G[c][2001]) * 100)}%",
              'g2020': p1(abs(GR[c][2020])), 'g2021': p1(GR[c][2021]), 'worst': p1(abs(GR[c][1983])), 'lit': p1(LIT[c][2024]), 'rem': usd(REM[c][L])})
claim(s, 'records; inflation lowest since 2001, peak 1968; four falls 1999-2002; worst 1983; record remittances; literacy 2024',
      peak(G, c) == L and peak(PC, c) == L and peak(PPP, c) == L and max(k for k in INF[c] if k < L and INF[c][k] <= INF[c][L]) == 2001 and peak(INF, c) == 1968 and all(GR[c][y] < 0 for y in range(1999, 2003)) and GR[c][1998] > 0
      and peak_low(GR, c) == 1983 and peak(REM, c) == L and max(LIT[c]) == 2024)

# ---------- Kyrgyzstan ----------
s, c = 'kyrgyzstan', 'KGZ'; t = common(s, c, None)
expect(t, s, {'grank': ordn(rank(GR, c)), 'g2024': p1(GR[c][2024]), 'g2022': p1(GR[c][2022]), 'x21': f"{G[c][L] / G[c][2021]:.1f} times", 'gdp2021': usd(G[c][2021]), 'rem%': p1(REMP[c][2024]), 'remrank': ordn(REMP_rank(c) if False else [k for k, _ in sorted(((k, v[2024]) for k, v in REMP.items() if k in econ and 2024 in v), key=lambda x: (-x[1], x[0]))].index(c) + 1),
              'rempeak%': p1(REMP[c][2021]), 'i2022': p1(INF[c][2022]), 'i2024': p1(INF[c][2024]), 'imax': p1(INF[c][1999]), 'worst': p1(abs(GR[c][1994])), 'g2020': p1(GR[c][2020])})
claim(s, '4th; 2024 best since 1988; 2022 and 2023 equal when rounded; records; rem share peak 2021, dollar peak 2022, ends 2024; inflation peak 1999 from 1996; worst 1994; growth from 1987, GDP from 1990',
      rank(GR, c) == 4 and max(k for k in GR[c] if k < 2024 and GR[c][k] >= GR[c][2024]) == 1988 and f'{GR[c][2022]:.1f}' == f'{GR[c][2023]:.1f}' and peak(G, c) == L and peak(PC, c) == L and peak(REMP, c) == 2021 and peak(REM, c) == 2022
      and max(REM[c]) == 2024 and peak(INF, c) == 1999 and min(INF[c]) == 1996 and peak_low(GR, c) == 1994 and min(GR[c]) == 1987 and min(G[c]) == 1990)

if bad:
    print('\n'.join(bad)); sys.exit(1)
print(f'{ok} checks matched the original World Bank files.')
