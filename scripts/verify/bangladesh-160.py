# Independent check of the Bangladesh hub (/country/bangladesh/) and health page (/country/bangladesh/health/),
# task 160. Reads the ORIGINAL UN WPP and World Bank files (never src/data/) and the built pages in dist/,
# recomputes every figure and rank the prose and JSON-LD use, and tests each claim.
#   python3 scripts/verify/bangladesh-160.py   (after npm run build)
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _wdi import wdi, rank_latest, ECON, expect, claim, report, usd, whole, p1, ordn, page_text
import _un as U

hub, hubt = page_text('dist/country/bangladesh/index.html')
hea, heat = page_text('dist/country/bangladesh/health/index.html')
def ld(p):
    g = [n for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', p, re.S) for n in json.loads(html.unescape(s)).get('@graph', [])]
    out = []
    for n in g:
        if n['@type'] in ('Article', 'Dataset'): out += [n.get('headline', ''), n.get('name', ''), n.get('description', '')]
        if n['@type'] == 'FAQPage': out += [x for q in n['mainEntity'] for x in (q['name'], q['acceptedAnswer']['text'])]
    return ' '.join(out)
c = lambda v: f"{round(v):,}"

def L(code):
    s = wdi(code)['BGD']; y = max(s); return y, s[y], wdi(code)

def rk(code, lowest=False):
    y, v, src = L(code)
    return rank_latest(src, 'BGD', y - 5, lowest_first=lowest)

# ---------------- hub ----------------
Y = 2026
pop = U.P('BGD', Y); dens = U.f('BGD', Y, 'PopDensity')
expect(hubt, 'hub', {'population': c(pop), 'density': c(dens), 'life expectancy': f"{U.f('BGD', Y, 'LEx'):.1f}"})
claim('hub', 'population 8th, seven countries or areas hold more', U.rank('BGD', Y) == 8)
dr = sorted(((float(v[Y]['PopDensity']), k) for k, v in U.raw.items() if k != 'WORLD' and Y in v), reverse=True)
claim('hub', 'density 9th on Earth', [k for _, k in dr].index('BGD') + 1 == 9)
denser = [k for d, k in dr if d > dens]
claim('hub', 'every denser place covers less than 1,200 km², incl. Singapore, Hong Kong, Malta', all(U.P(k, Y) / U.f(k, Y, 'PopDensity') < 1200 for k in denser) and {'SGP', 'HKG', 'MLT'} <= set(denser))
big = sorted(((float(v[Y]['PopDensity']), k) for k, v in U.raw.items() if k != 'WORLD' and Y in v and U.P(k, Y) > 10e6), reverse=True)
claim('hub', 'most crowded country of over 10 million, Taiwan next at under half', big[0][1] == 'BGD' and big[1][1] == 'TWN' and big[1][0] < big[0][0] / 2)

y, land, _ = L('AG.LND.TOTL.K2'); expect(hubt, 'hub', {'land area': c(land)})
y, g, _ = L('NY.GDP.MKTP.CD'); expect(hubt, 'hub', {'GDP': usd(g), 'GDP year': str(y)})
y, gpc, _ = L('NY.GDP.PCAP.CD'); expect(hubt, 'hub', {'GDP per person': whole(gpc)})
y, rem, _ = L('BX.TRF.PWKR.CD.DT'); expect(hubt, 'hub', {'remittances': usd(rem)}); claim('hub', 'remittances 7th largest', rk('BX.TRF.PWKR.CD.DT')[0] == 7)
y, mf, _ = L('NV.IND.MANF.ZS'); expect(hubt, 'hub', {'manufacturing': p1(mf)}); claim('hub', 'manufacturing share 12th highest', rk('NV.IND.MANF.ZS')[0] == 12)
y, ar, _ = L('AG.LND.ARBL.ZS'); expect(hubt, 'hub', {'arable': p1(ar)}); claim('hub', 'highest arable share in the world', rk('AG.LND.ARBL.ZS')[0] == 1)
y, ag, _ = L('AG.LND.AGRI.ZS'); expect(hubt, 'hub', {'agricultural land': p1(ag)})
y, apc, _ = L('AG.LND.ARBL.HA.PC'); expect(hubt, 'hub', {'arable per person': f"{apc:.2f}"})
y, cer, _ = L('AG.YLD.CREL.KG'); r, n = rk('AG.YLD.CREL.KG'); expect(hubt, 'hub', {'cereal yield': c(cer), 'cereal rank': f"{ordn(r)} of {n}"})
y, hg, _ = L('SH.XPD.CHEX.GD.ZS'); r, n = rk('SH.XPD.CHEX.GD.ZS'); expect(hubt, 'hub', {'health spending': p1(hg)}); claim('hub', 'second-lowest health spending share', r == n - 1)
y, oop, _ = L('SH.XPD.OOPC.CH.ZS'); r, n = rk('SH.XPD.OOPC.CH.ZS', True); expect(hubt, 'hub', {'out of pocket': p1(oop)}); claim('hub', 'second-highest out-of-pocket share', r == n - 1)
y, pm, _ = L('EN.ATM.PM25.MC.M3'); r, n = rk('EN.ATM.PM25.MC.M3', True); expect(hubt, 'hub', {'PM2.5': f"{pm:.1f}", 'PM2.5 count': f"third worst of {n}"}); claim('hub', 'third-worst PM2.5', r == n - 2)
y, u5, _ = L('SH.DYN.MORT'); expect(hubt, 'hub', {'under-5': f"{u5:.1f}"})
y, subs, _ = L('IT.CEL.SETS'); expect(hubt, 'hub', {'mobile subscriptions': c(subs)}); claim('hub', 'mobile subscriptions 9th', rk('IT.CEL.SETS')[0] == 9)
y, net, _ = L('IT.NET.USER.ZS'); expect(hubt, 'hub', {'internet': p1(net)}); claim('hub', 'more than half online', net > 50)
y, el, _ = L('EG.ELC.ACCS.ZS'); expect(hubt, 'hub', {'electricity': p1(el)})
y, cc, _ = L('EG.CFT.ACCS.ZS'); expect(hubt, 'hub', {'clean cooking': p1(cc)})
y, ea, _ = L('SL.AGR.EMPL.ZS'); expect(hubt, 'hub', {'jobs in agriculture': p1(ea)})
claim('hub', 'labour force 8th', rk('SL.TLF.TOTL.IN')[0] == 8)
y, fx, _ = L('PA.NUS.FCRF'); expect(hubt, 'hub', {'exchange rate': f"{fx:.2f}"})
y, hpc, _ = L('SH.XPD.CHEX.PC.CD'); expect(hubt, 'hub', {'health per person': whole(hpc)})
for num in re.findall(r'\d[\d,]*(?:\.\d+)?', ld(hub)):
    claim('hub', f'JSON-LD number {num} on page', num in hubt)

# ---------------- health ----------------
s = lambda code: wdi(code)['BGD']
U5, NEO, MAT, INF = s('SH.DYN.MORT'), s('SH.DYN.NMRT'), s('SH.STA.MMRT'), s('SP.DYN.IMRT.IN')
DOC, NUR, BED = s('SH.MED.PHYS.ZS'), s('SH.MED.NUMW.P3'), s('SH.MED.BEDS.ZS')
OOP, HG, HPC = s('SH.XPD.OOPC.CH.ZS'), s('SH.XPD.CHEX.GD.ZS'), s('SH.XPD.CHEX.PC.CD')
MEA, DPT, STU, UND, DIA, TOB = s('SH.IMM.MEAS'), s('SH.IMM.IDPT'), s('SH.STA.STNT.ZS'), s('SN.ITK.DEFC.ZS'), s('SH.STA.DIAB.ZS'), s('SH.PRV.SMOK')
ly = lambda d: max(d)
expect(heat, 'health', {
  'under-5': f"{U5[2024]:.1f}", 'under-5 1990': f"{U5[1990]:.1f}", 'infant': f"{INF[2024]:.1f}", 'newborn': f"{NEO[2024]:.1f}",
  'maternal': f"{round(MAT[2023])}", 'maternal 2000': f"{round(MAT[2000])}", 'maternal 2020': f"{round(MAT[2020])}", 'maternal 2021': f"{round(MAT[2021])}", 'maternal 2022': f"{round(MAT[2022])}",
  'out of pocket': p1(OOP[2023]), 'out of pocket 2000': p1(OOP[2000]), 'health % GDP': p1(HG[2023]), 'health per person': whole(HPC[2023]),
  'doctors': f"{DOC[2023]:.2f}", 'nurses': f"{NUR[2023]:.2f}", 'beds': f"{BED[ly(BED)]:.1f}",
  'measles': p1(MEA[2024]), 'DPT': p1(DPT[2024]), 'stunting': p1(STU[2022]), 'stunting 2000': p1(STU[2000]), 'undernourishment': p1(UND[2024]),
  'diabetes': p1(DIA[2024]), 'tobacco': p1(TOB[2024]), 'tobacco 2000': p1(TOB[2000]),
  'drop 2015-19': f"{U5[2015] - U5[2019]:.1f}", 'drop 2020-24': f"{U5[2020] - U5[2024]:.1f}", 'newborn share': p1(NEO[2024] / U5[2024] * 100),
  'one doctor per': f"{round(1000 / DOC[2023]):,}",
})
claim('health', 'about a fifth of the 1990 rate', 0.19 < U5[2024] / U5[1990] < 0.22)
claim('health', 'maternal rose in 2021 then fell', MAT[2021] > MAT[2020] and MAT[2022] < MAT[2020] and MAT[2023] < MAT[2022])
claim('health', 'out-of-pocket highest since 2000', all(v < OOP[2023] for y, v in OOP.items() if y != 2023) and min(OOP) == 2000)
claim('health', 'fewer nurses than doctors', NUR[2023] < DOC[2023])
claim('health', 'doctors four times 1990', 3.9 < DOC[2023] / DOC[1990] < 4.1)
claim('health', 'measles 65% in 1990', MEA[1990] == 65); expect(heat, 'health', {'measles 1990': p1(MEA[1990])})
claim('health', 'stunting under half of 2000', STU[2022] < STU[2000] / 2 + 0.1)
claim('health', 'undernourishment lowest since 2001', min(UND) == 2001 and all(v > UND[2024] for y, v in UND.items() if y != 2024))
docs, nurs = wdi('SH.MED.PHYS.ZS'), wdi('SH.MED.NUMW.P3')
pairs = []
for k in ECON:
    d, n_ = docs.get(k, {}), nurs.get(k, {})
    ys = [y for y in d if y >= 2018 and y in n_]
    if ys: y = max(ys); pairs.append(n_[y] > d[y])
claim('health', '161 of 173 have more nurses', len(pairs) == 173 and sum(pairs) == 161)
expect(heat, 'health', {'nurse count': '173 countries', 'more nurses': '161 have more nurses'})
r, n = rank_latest(wdi('SH.DYN.MORT'), 'BGD', 2019, lowest_first=False)
expect(heat, 'health', {'under-5 rank': f"{ordn(r)} highest of {n}"})
for num in re.findall(r'\d[\d,]*(?:\.\d+)?', ld(hea)):
    claim('health', f'JSON-LD number {num} on page', num in heat)
report()
