# Independent check of the task 171 pages: hub (/country/<slug>/) and health page (/country/<slug>/health/) for
# Japan, Philippines, Egypt, DR Congo, Vietnam, Iran, Turkey, Germany, Thailand and United Kingdom.
# Reads the ORIGINAL UN WPP / WUP and World Bank files (never src/data/wpp, src/data/wdi or the profiles) and the
# built pages in dist/. Checks:
#   1. every World Bank and UN statistic row on both pages (value, year, world rank) against the original files;
#   2. every cell of the yearly health table against the original World Bank files;
#   3. every number in the JSON-LD (headline, descriptions, FAQ) appears on the page;
#   4. the claims each page makes in its text, recomputed from the original files.
# Energy (Ember / Global Carbon Budget) rows are compared with their originals by check-energy, country facts by
# check-facts; they are only counted here.
#   python3 scripts/verify/batch-171.py   (after npm run build)
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _wdi import wdi, ECON, claim, report, ordn, page_text
import _wdi
import _un as U

COUNTRIES = [('japan', 'JPN'), ('philippines', 'PHL'), ('egypt', 'EGY'), ('dr-congo', 'COD'), ('vietnam', 'VNM'),
             ('iran', 'IRN'), ('turkey', 'TUR'), ('germany', 'DEU'), ('thailand', 'THA'), ('united-kingdom', 'GBR')]
Y = 2026

# catalogue: statistic id -> how it is made (configuration only; the values come from the original files)
cat = {}
for sec in json.load(open('src/data/profile-stats.json'))['sections']:
    for st in sec['stats']:
        if 'id' in st and not st.get('planned'): cat[f"{sec['id']}.{st['id']}"] = st
code_of = dict((k, c) for c, k in re.findall(r"'([A-Z0-9.]+)': \{ key: '(\w+)'", open('scripts/build-wdi.mjs').read()))
_cache = {}
def W(key):
    c = code_of[key]
    if c not in _cache: _cache[c] = wdi(c)
    return _cache[c]
def V(key, iso, y): return W(key)[iso][y]
def S(key, iso): return W(key)[iso]

from decimal import Decimal, ROUND_HALF_UP
def hu(v, d):  # round half up, like JavaScript's toFixed / Math.round on these values
    return Decimal(v).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)  # exact binary value, ties up (JS toFixed)
fmt = {
    'int': lambda v: f"{hu(v, 0):,}", 'pct': lambda v: f"{hu(v, 1)}%".replace('-0.0%', '0.0%'), 'dec1': lambda v: f"{hu(v, 1)}", 'dec2': lambda v: f"{hu(v, 2)}",
    'usd': _wdi.usd, 'usdWhole': lambda v: f"${round(v):,}", 'intd': lambda v: f"Int${round(v):,}",
}
def rank_wdi(key, iso, year, low, since=None):
    src = W(key); s0 = since or year - 5
    vals = {k: v[max(y for y in v if y >= s0)] for k, v in src.items() if k in ECON and any(y >= s0 for y in v)}
    order = sorted(vals.items(), key=lambda kv: ((kv[1] if low else -kv[1]), kv[0]))
    if iso not in vals: return None, len(order)   # latest value older than the ranking window: no rank shown
    return [k for k, _ in order].index(iso) + 1, len(order)

UNCOL = {'growthRatePct': ('PopGrowthRate', 1), 'densityPerKm2': ('PopDensity', 1), 'medianAge': ('MedianAgePop', 1),
         'fertility': ('TFR', 1), 'lifeExpectancy': ('LEx', 1), 'births': ('Births', 1000), 'deaths': ('Deaths', 1000), 'netMigrants': ('NetMigrations', 1000)}
def un_value(key, iso):
    if key == 'population': return U.P(iso, Y)
    if key == 'urbanPct': return float(U.urban(iso)[Y])
    col, k = UNCOL[key]; return U.f(iso, Y, col) * k
def un_rank(key, iso, low):
    col = 'TPopulation1July' if key == 'population' else 'PopDensity'
    vals = {k: float(v[Y][col]) for k, v in U.raw.items() if k != 'WORLD' and Y in v and v[Y][col]}
    order = sorted(vals.items(), key=lambda kv: ((kv[1] if low else -kv[1]), kv[0]))
    return [k for k, _ in order].index(iso) + 1, len(order)

def ld_text(p):
    out = []
    for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', p, re.S):
        for n in json.loads(html.unescape(s)).get('@graph', []):
            if n['@type'] in ('Article', 'Dataset'): out += [n.get('headline', ''), n.get('name', ''), n.get('description', '')]
            if n['@type'] == 'FAQPage': out += [x for q in n['mainEntity'] for x in (q['name'], q['acceptedAnswer']['text'])]
    return out

counts = {'wdi rows': 0, 'un rows': 0, 'other rows': 0, 'table cells': 0, 'json-ld numbers': 0, 'claims': 0}
def rows_check(slug, iso, p):
    for m in re.finditer(r'<tr data-stat="([\w.]+)"[^>]*>(.*?)</tr>', p, re.S):
        sid, body = m.group(1), m.group(2)
        cells = [html.unescape(re.sub(r'<[^>]+>', '', x)).strip() for x in re.findall(r'<td class="(?:sl-v|sl-y|sl-r)"[^>]*>(.*?)</td>', body, re.S)]
        val = html.unescape(re.sub(r'<[^>]+>', '', re.search(r'data-value[^>]*>(.*?)</span>', body, re.S).group(1))).strip()
        year, rk = (cells[1], cells[2]) if len(cells) >= 3 else ('', '')
        st = cat.get(sid)
        if st and st['src'] == 'wdi':
            s = S(st['key'], iso); y = max(s)
            claim(slug, f'{sid} year {year} = latest {y}', str(y) == year and y >= 2000)
            claim(slug, f'{sid} value {val} = {fmt[st["fmt"]](s[y])}', val == fmt[st['fmt']](s[y]))
            if st.get('rank'):
                r, n = rank_wdi(st['key'], iso, y, st['rank'] == 'low', st.get('since'))
                want = f"{ordn(r)} {'lowest' if st['rank'] == 'low' else 'highest'} of {n}" if r else ''
                claim(slug, f'{sid} rank {rk!r} = {want!r}', rk == want)
            counts['wdi rows'] += 1
        elif st and st['src'] == 'wpp':
            v = un_value(st['key'], iso)
            claim(slug, f'{sid} value {val} = {fmt[st["fmt"]](v)}', val == fmt[st['fmt']](v))
            if st.get('rank'):
                r, n = un_rank(st['key'], iso, st['rank'] == 'low')
                claim(slug, f'{sid} rank', rk == f"{ordn(r)} {'lowest' if st['rank'] == 'low' else 'highest'} of {n}")
            counts['un rows'] += 1
        else:
            counts['other rows'] += 1

HCOL = {'u5': ('under5Mortality', 1), 'infant': ('infantMortality', 1), 'neonatal': ('neonatalMortality', 1), 'maternal': ('maternalMortality', 0),
        'measles': ('measlesVaccPct', 0), 'healthGdp': ('healthSpendPctGdp', 1), 'oop': ('outOfPocketPct', 1)}
def table_check(slug, iso, p):
    for m in re.finditer(r'<tr[^>]*data-year="(\d+)"[^>]*>(.*?)</tr>', p, re.S):
        y = int(m.group(1))
        for col, cell in re.findall(r'data-col="(\w+)"[^>]*>(.*?)</td>', m.group(2), re.S):
            key, d = HCOL[col]; s = S(key, iso)
            want = f"{s[y]:,.{d}f}" if y in s else '–'
            claim(slug, f'table {y} {col} {cell!r} = {want!r}', html.unescape(cell).strip() == want)
            counts['table cells'] += 1

def ld_check(slug, p, t):
    for txt in ld_text(p):
        for num in re.findall(r'\d[\d,]*(?:\.\d+)?', txt):
            num = num.rstrip(','); claim(slug, f'JSON-LD number {num} on page', num in t); counts['json-ld numbers'] += 1

pages = {}
for slug, iso in COUNTRIES:
    for kind, path in (('hub', f'dist/country/{slug}/index.html'), ('health', f'dist/country/{slug}/health/index.html')):
        p, t = page_text(path); pages[(slug, kind)] = t
        rows_check(f'{slug}/{kind}', iso, p); ld_check(f'{slug}/{kind}', p, t)
        if kind == 'health': table_check(f'{slug}/{kind}', iso, p)

# ---------------- claims in the text, recomputed ----------------
def C(slug, what, ok): claim(slug, what, ok); counts['claims'] += 1
since_of = {st['key']: st.get('since') for st in cat.values() if st['src'] == 'wdi'}
R = lambda key, iso, low=False: rank_wdi(key, iso, max(S(key, iso)), low, since_of.get(key))
rank_by = {st['key']: st.get('rank') for st in cat.values() if st['src'] == 'wdi'}
# place from the top / bottom exactly as the site counts it: from the catalogue's ranking direction, ties broken by ISO3 code
def top(key, iso):
    if rank_by.get(key) == 'low': r, n = R(key, iso, True); return n - r + 1
    return R(key, iso)[0]
def bottom(key, iso):
    if rank_by.get(key) == 'low': return R(key, iso, True)[0]
    r, n = R(key, iso); return n - r + 1
L = lambda key, iso: S(key, iso)[max(S(key, iso))]
pop = {k: U.P(k, Y) for k, v in U.raw.items() if k != 'WORLD' and Y in v}
e0 = lambda k: U.f(k, Y, 'LEx')

rank_pop = sorted(pop, key=pop.get, reverse=True)
big = sorted(((U.f(k, Y, 'LEx'), k) for k in pop if pop[k] > 100e6), reverse=True)
growB = sorted(((U.f(k, Y, 'PopGrowthRate'), k) for k in pop if pop[k] > 100e6), reverse=True)
ageB = sorted((U.f(k, Y, 'MedianAgePop'), k) for k in pop if pop[k] > 100e6)
age50 = sorted(((U.f(k, Y, 'MedianAgePop'), k) for k in pop if pop[k] > 50e6), reverse=True)
H = lambda slug: pages[(slug, 'hub')]
T = lambda slug: pages[(slug, 'health')]

# Japan
C('japan', 'longest life expectancy of 100M+ countries by >5 years, runner-up USA', big[0][1] == 'JPN' and big[0][0] - big[1][0] > 5 and big[1][1] == 'USA')
C('japan', 'oldest median age of countries over 50 million', age50[0][1] == 'JPN')
C('japan', 'deaths > 2x births, median > 50', U.K('JPN', Y, 'Deaths') > 2 * U.K('JPN', Y, 'Births') and U.f('JPN', Y, 'MedianAgePop') > 50)
C('japan', '4th GDP behind USA, CHN, DEU; 3rd reserves; growth < 1.5%', top('gdp', 'JPN') == 4 and {top('gdp', k) for k in ('USA', 'CHN', 'DEU')} == {1, 2, 3} and top('reserves', 'JPN') == 3 and L('gdpGrowthPct', 'JPN') < 1.5)
C('japan', '6th R&D, 3rd resident patents, 5th-lowest homicide, forest 20th >68%, 5th CO2', top('rdSpendPctGdp', 'JPN') == 6 and top('patentsResident', 'JPN') == 3 and bottom('homicideRate', 'JPN') == 5 and top('forestPct', 'JPN') == 20 and L('forestPct', 'JPN') > 68)
C('japan/health', '4th-lowest infant, 5th-lowest newborn, 7th-lowest under-five', bottom('infantMortality', 'JPN') == 4 and bottom('neonatalMortality', 'JPN') == 5 and bottom('under5Mortality', 'JPN') == 7)
C('japan/health', '3rd beds >12; ~5 nurses per doctor', top('hospitalBedsPer1000', 'JPN') == 3 and L('hospitalBedsPer1000', 'JPN') > 12 and 4.8 < V('nursesPer1000', 'JPN', 2022) / V('doctorsPer1000', 'JPN', 2022) < 5)
hg = S('healthSpendPctGdp', 'JPN'); C('japan/health', 'health share peaked 2022, now >1.5 points lower, 20th', max(hg, key=hg.get) == 2022 and hg[2023] < hg[2022] - 1.5 and top('healthSpendPctGdp', 'JPN') == 20)
C('japan/health', 'tobacco nearly halved; maternal < 1/4 of 1990; DPT 7th', 0.5 < L('tobaccoPct', 'JPN') / V('tobaccoPct', 'JPN', 2000) < 0.55 and V('maternalMortality', 'JPN', 1990) / V('maternalMortality', 'JPN', 2023) > 4 and top('dptVaccPct', 'JPN') == 7)

# Philippines
C('philippines', '14th population, 4th remittances >8% GDP, 4th high-tech >60%', rank_pop[13] == 'PHL' and top('remittances', 'PHL') == 4 and L('remittancesPctGdp', 'PHL') > 8 and top('hiTechExportsPct', 'PHL') == 4 and L('hiTechExportsPct', 'PHL') > 60)
C('philippines', 'women >14 points ahead on accounts', L('accountFemalePct', 'PHL') - L('accountMalePct', 'PHL') > 14)
C('philippines', '8th out of school, literacy >98%, 3rd-lowest migrant share', top('outOfSchoolPrimary', 'PHL') == 8 and L('literacyPct', 'PHL') > 98 and bottom('migrantPct', 'PHL') == 3)
tb = S('tbIncidence', 'PHL'); C('philippines/health', 'TB 3rd, above 2000; low year on page', top('tbIncidence', 'PHL') == 3 and tb[2024] > tb[2000] and f'fell to {tb[min(tb, key=tb.get)]:.0f} in {min(tb, key=tb.get)}' in T('philippines'))
m = S('maternalMortality', 'PHL'); C('philippines/health', 'maternal +70% in 2021, now below 2020', m[2021] > 1.7 * m[2020] and m[2023] < m[2020])
mv = S('measlesVaccPct', 'PHL'); C('philippines/health', 'measles 2021 lowest since 1990, 80% now; DPT 27th lowest', mv[2021] == min(v for y, v in mv.items() if y >= 1990) and mv[2024] == 80 and bottom('dptVaccPct', 'PHL') == 27)
C('philippines/health', '~6 nurses per doctor; stunting >25%, 27th, -16 points since 1990; u5 -<3.5 since 2010', 6 < V('nursesPer1000', 'PHL', 2021) / V('doctorsPer1000', 'PHL', 2021) < 6.1 and L('stuntingPct', 'PHL') > 25 and top('stuntingPct', 'PHL') == 27 and V('stuntingPct', 'PHL', 1990) - L('stuntingPct', 'PHL') > 16 and V('under5Mortality', 'PHL', 2010) - L('under5Mortality', 'PHL') < 3.5)

# Egypt
C('egypt', '13th population, fertility >2.5', rank_pop[12] == 'EGY' and U.f('EGY', Y, 'TFR') > 2.5)
C('egypt', 'water withdrawals top, >7000%, times on page', top('freshwaterWithdrawPct', 'EGY') == 1 and L('freshwaterWithdrawPct', 'EGY') > 7000 and f"about {int(L('freshwaterWithdrawPct', 'EGY') // 100)} times" in H('egypt'))
C('egypt', 'farmland <5%, forest 5th lowest, fertiliser 8th, cereal 11th', L('agriLandPct', 'EGY') < 5 and bottom('forestPct', 'EGY') == 5 and top('fertiliserKgHa', 'EGY') == 8 and top('cerealYield', 'EGY') == 11)
C('egypt', '5th remittances >11% GDP; women 9th lowest <20%; inflation 15th', top('remittances', 'EGY') == 5 and L('remittancesPctGdp', 'EGY') > 11 and bottom('lfpFemale', 'EGY') == 9 and L('lfpFemale', 'EGY') < 20 and top('inflationPct', 'EGY') == 15)
C('egypt/health', 'diabetes 9th >22%', top('diabetesPct', 'EGY') == 9 and L('diabetesPct', 'EGY') > 22)
tob = S('tobaccoPct', 'EGY'); ys = sorted(tob)
tw = W('tobaccoPct'); both = [k for k in ECON if 2000 in tw.get(k, {}) and 2024 in tw.get(k, {})]; rose = [k for k in both if tw[k][2024] > tw[k][2000]]
C('egypt/health', 'tobacco up at every step; one of 18 risers', all(tob[b] > tob[a] for a, b in zip(ys, ys[1:])) and 'EGY' in rose and len(rose) == 18 and f'one of just {len(rose)}' in T('egypt') and f'Of the {len(both)} countries' in T('egypt'))
C('egypt/health', 'out of pocket >55%, 21st', L('outOfPocketPct', 'EGY') > 55 and top('outOfPocketPct', 'EGY') == 21)
m = S('maternalMortality', 'EGY'); C('egypt/health', 'maternal >2x 2019 in 2021, now below 2019', m[2021] > 2 * m[2019] and m[2023] < m[2019])
C('egypt/health', 'u5 <1/3.5 of 1990; stunting ~halved; undernourishment +1.5 since 2019; measles 97', L('under5Mortality', 'EGY') < V('under5Mortality', 'EGY', 1990) / 3.5 and L('stuntingPct', 'EGY') < 0.55 * V('stuntingPct', 'EGY', 2000) and L('undernourishedPct', 'EGY') > V('undernourishedPct', 'EGY', 2019) + 1.5 and L('measlesVaccPct', 'EGY') == 97)

# DR Congo
C('dr-congo', 'fastest-growing and youngest of 100M+', growB[0][1] == 'COD' and ageB[0][1] == 'COD')
C('dr-congo', '15th population, fertility >5.5', rank_pop[14] == 'COD' and U.f('COD', Y, 'TFR') > 5.5)
C('dr-congo', 'highest extreme poverty >85%', top('povertyExtremePct', 'COD') == 1 and L('povertyExtremePct', 'COD') > 85)
C('dr-congo', 'lowest basic water; 7th-lowest electricity <25%', bottom('basicWaterPct', 'COD') == 1 and bottom('electricityAccessPct', 'COD') == 7 and L('electricityAccessPct', 'COD') < 25)
C('dr-congo', '6th forest >60%; 9th-lowest GDP per person', top('forestArea', 'COD') == 6 and L('forestPct', 'COD') > 60 and bottom('gdpPerCapita', 'COD') == 9)
u5 = S('under5Mortality', 'COD'); C('dr-congo/health', 'u5 8th; 2000 > 1990; <3 below 2015', top('under5Mortality', 'COD') == 8 and u5[2000] > u5[1990] and u5[2024] > u5[2015] - 3)
C('dr-congo/health', 'undernourishment and stunting 6th; stunting above 2010; undernourishment >39%', top('undernourishedPct', 'COD') == 6 and top('stuntingPct', 'COD') == 6 and L('stuntingPct', 'COD') > V('stuntingPct', 'COD', 2010) and L('undernourishedPct', 'COD') > 39)
C('dr-congo/health', 'malaria 5th, spending 4th lowest, measles 10th lowest, road 10th, maternal 13th', top('malariaIncidence', 'COD') == 5 and bottom('healthSpendPerCapita', 'COD') == 4 and bottom('measlesVaccPct', 'COD') == 10 and top('roadDeathsPer100k', 'COD') == 10 and top('maternalMortality', 'COD') == 13)
C('dr-congo/health', 'one doctor per 4,700–4,900', 4700 < 1000 / L('doctorsPer1000', 'COD') < 4900)

# Vietnam
C('vietnam', '16th population, crossed 100 million before this year', rank_pop[15] == 'VNM' and any(U.P('VNM', y) > 100e6 for y in range(2015, Y)))
C('vietnam', 'exports 9th >95% GDP, high-tech 11th, ports 6th', top('exportsPctGdp', 'VNM') == 9 and L('exportsPctGdp', 'VNM') > 95 and top('hiTechExportsPct', 'VNM') == 11 and top('containerTeu', 'VNM') == 6)
C('vietnam', 'growth 12th >=8%', top('gdpGrowthPct', 'VNM') == 12 and L('gdpGrowthPct', 'VNM') >= 8)
C('vietnam', 'industry jobs 5th ~1/3, unemployment 11th lowest, women 20th', top('empIndPct', 'VNM') == 5 and 33 < L('empIndPct', 'VNM') < 36 and bottom('unemploymentPct', 'VNM') == 11 and top('lfpFemale', 'VNM') == 20)
C('vietnam', 'national poverty 4th lowest, fertiliser 11th', bottom('povertyNationalPct', 'VNM') == 4 and top('fertiliserKgHa', 'VNM') == 11)
C('vietnam/health', 'diabetes 10th lowest <4%, road 22nd >30', bottom('diabetesPct', 'VNM') == 10 and L('diabetesPct', 'VNM') < 4 and top('roadDeathsPer100k', 'VNM') == 22 and L('roadDeathsPer100k', 'VNM') > 30)
mv = S('measlesVaccPct', 'VNM'); C('vietnam/health', 'measles 97 → 82 → 98, 30th', (mv[2020], mv[2023], mv[2024]) == (97, 82, 98) and top('measlesVaccPct', 'VNM') == 30)
o = S('outOfPocketPct', 'VNM'); C('vietnam/health', 'stunting < half 2000; oop peak 2019, now >5 lower; u5 ~1/3 of 1990', L('stuntingPct', 'VNM') < V('stuntingPct', 'VNM', 2000) / 2 and max(o, key=o.get) == 2019 and o[2023] < o[2019] - 5 and 2.8 < V('under5Mortality', 'VNM', 1990) / L('under5Mortality', 'VNM') < 3.2)

# Iran
C('iran', '17th population', rank_pop[16] == 'IRN')
C('iran', 'inflation 5th >40%, growth 4th weakest <0', top('inflationPct', 'IRN') == 5 and L('inflationPct', 'IRN') > 40 and bottom('gdpGrowthPct', 'IRN') == 4 and L('gdpGrowthPct', 'IRN') < 0)
C('iran', "women's participation 5th lowest; women MPs 11th lowest <5%", bottom('lfpFemale', 'IRN') == 5 and bottom('womenParliamentPct', 'IRN') == 11 and L('womenParliamentPct', 'IRN') < 5)
C('iran', 'migrants 17th, external debt ratio 3rd lowest, articles 14th', top('migrantStock', 'IRN') == 17 and bottom('externalDebtPctGni', 'IRN') == 3 and top('journalArticles', 'IRN') == 14)
mv = S('measlesVaccPct', 'IRN'); since = max(y for y, v in mv.items() if v < 99) + 1
C('iran/health', 'measles 99% every year since 2014, 7th', since == 2014 and L('measlesVaccPct', 'IRN') == 99 and top('measlesVaccPct', 'IRN') == 7)
m = S('maternalMortality', 'IRN'); C('iran/health', 'maternal 2.5–3x 2019 in 2021, now below 2019', 2.5 * m[2019] < m[2021] < 3 * m[2019] and m[2023] < m[2019])
C('iran/health', 'u5 about a fifth of 1990; oop +5 since 2020; doctors +60% since 2015; tobacco ~halved', 0.18 < L('under5Mortality', 'IRN') / V('under5Mortality', 'IRN', 1990) < 0.21 and V('outOfPocketPct', 'IRN', 2023) > V('outOfPocketPct', 'IRN', 2020) + 5 and V('doctorsPer1000', 'IRN', 2023) > 1.6 * V('doctorsPer1000', 'IRN', 2015) and L('tobaccoPct', 'IRN') < 0.52 * V('tobaccoPct', 'IRN', 2000))

# Turkey
C('turkey', '18th population, 11th migrants >8%', rank_pop[17] == 'TUR' and top('migrantStock', 'TUR') == 11 and L('migrantPct', 'TUR') > 8)
C('turkey', 'inflation 6th >30%, external debt 5th', top('inflationPct', 'TUR') == 6 and L('inflationPct', 'TUR') > 30 and top('externalDebt', 'TUR') == 5)
C('turkey', 'air 5th, tourists 15th, receipts 12th', top('airPassengers', 'TUR') == 5 and top('touristArrivals', 'TUR') == 15 and top('tourismReceipts', 'TUR') == 12)
C('turkey', 'tertiary 10th >100%, patents 10th, net emigration, women <40%', top('tertiaryEnrolPct', 'TUR') == 10 and L('tertiaryEnrolPct', 'TUR') > 100 and top('patentsResident', 'TUR') == 10 and U.K('TUR', Y, 'NetMigrations') < 0 and L('lfpFemale', 'TUR') < 40)
u5 = S('under5Mortality', 'TUR'); f = [u5[y] for y in range(1990, 2023)]
C('turkey/health', 'u5 fell every year 1990–2022, +30% in 2023, below 2022 in 2024', all(b < a for a, b in zip(f, f[1:])) and u5[2023] > 1.3 * u5[2022] and u5[2024] < u5[2022])
C('turkey/health', 'newborn kept falling 2023–24', V('neonatalMortality', 'TUR', 2023) < V('neonatalMortality', 'TUR', 2022) and V('neonatalMortality', 'TUR', 2024) < V('neonatalMortality', 'TUR', 2023))
C('turkey/health', 'tobacco 25th >30%, down <2; diabetes 29th 15.5–17.5%', top('tobaccoPct', 'TUR') == 25 and L('tobaccoPct', 'TUR') > 30 and V('tobaccoPct', 'TUR', 2000) - L('tobaccoPct', 'TUR') < 2 and top('diabetesPct', 'TUR') == 29 and 15.5 < L('diabetesPct', 'TUR') < 17.5)
C('turkey/health', 'doctors 2.4–2.6x 1990; oop -9 since 2000; DPT 18th', 2.4 < V('doctorsPer1000', 'TUR', 2022) / V('doctorsPer1000', 'TUR', 1990) < 2.6 and L('outOfPocketPct', 'TUR') < V('outOfPocketPct', 'TUR', 2000) - 9 and top('dptVaccPct', 'TUR') == 18)

# Germany
C('germany', 'migrants 2nd after USA, >19%, net immigration', top('migrantStock', 'USA') == 1 and top('migrantStock', 'DEU') == 2 and L('migrantPct', 'DEU') > 19 and U.K('DEU', Y, 'NetMigrations') > 0)
C('germany', 'deaths >1.4x births', U.K('DEU', Y, 'Deaths') > 1.4 * U.K('DEU', Y, 'Births'))
C('germany', '3rd GDP, growth 19th weakest <0.5, 3rd exporter and importer', top('gdp', 'DEU') == 3 and bottom('gdpGrowthPct', 'DEU') == 19 and L('gdpGrowthPct', 'DEU') < 0.5 and top('exports', 'DEU') == 3 and top('imports', 'DEU') == 3)
C('germany', 'protected 12th >=40%; tourism receipts 2nd; LPI 4th; FDI 4th; articles 4th', top('protectedPct', 'DEU') == 12 and L('protectedPct', 'DEU') >= 40 and top('tourismReceipts', 'DEU') == 2 and top('logisticsIndex', 'DEU') == 4 and top('fdiInflows', 'DEU') == 4 and top('journalArticles', 'DEU') == 4)
C('germany/health', 'beds 7th, nurses 12th, doctors 15th; share 9th, per person 10th', top('hospitalBedsPer1000', 'DEU') == 7 and top('nursesPer1000', 'DEU') == 12 and top('doctorsPer1000', 'DEU') == 15 and top('healthSpendPctGdp', 'DEU') == 9 and top('healthSpendPerCapita', 'DEU') == 10)
C('germany/health', 'newborn flat since 2010, u5 flat since 2019', all(v == 2.3 for y, v in S('neonatalMortality', 'DEU').items() if y >= 2010) and all(v == 3.7 for y, v in S('under5Mortality', 'DEU').items() if y >= 2019))
C('germany/health', 'DPT below measles and 2021, rank >100; tobacco -12', L('dptVaccPct', 'DEU') < L('measlesVaccPct', 'DEU') and L('dptVaccPct', 'DEU') < V('dptVaccPct', 'DEU', 2021) and top('dptVaccPct', 'DEU') > 100 and V('tobaccoPct', 'DEU', 2000) - L('tobaccoPct', 'DEU') > 12)

# Thailand
C('thailand', 'deaths > births, shrinking, fertility <1.2', U.K('THA', Y, 'Deaths') > U.K('THA', Y, 'Births') and U.f('THA', Y, 'PopGrowthRate') < 0 and U.f('THA', Y, 'TFR') < 1.2)
lowerTfr = sum(1 for k in pop if round(U.f(k, Y, 'TFR'), 2) < round(U.f('THA', Y, 'TFR'), 2))
infl = W('inflationPct'); neg = sum(1 for k in pop if k in infl and infl[k] and max(infl[k]) >= 2000 and infl[k][max(infl[k])] < 0)
C('thailand', f'{lowerTfr} lower fertility; {neg} negative inflation readings, numbers on page', f'only {lowerTfr} countries or areas are lower' in H('thailand') and f'one of only {neg} negative readings' in H('thailand'))
C('thailand', 'tourists 5th (2019), unemployment 4th lowest <1%, exports 27th, high-tech 19th', top('touristArrivals', 'THA') == 5 and bottom('unemploymentPct', 'THA') == 4 and L('unemploymentPct', 'THA') < 1 and top('exportsPctGdp', 'THA') == 27 and top('hiTechExportsPct', 'THA') == 19)
C('thailand/health', 'road 17th >32; oop >34% → <10%, 24th lowest', top('roadDeathsPer100k', 'THA') == 17 and L('roadDeathsPer100k', 'THA') > 32 and V('outOfPocketPct', 'THA', 2000) > 34 and L('outOfPocketPct', 'THA') < 10 and bottom('outOfPocketPct', 'THA') == 24)
m = S('maternalMortality', 'THA'); C('thailand/health', 'maternal 2.9–3x in 2022, below 2021 in 2023', 2.9 * m[2021] < m[2022] < 3 * m[2021] and m[2023] < m[2021])
C('thailand/health', 'nurses >6.5x doctors; u5 <1/4 1990; diabetes ~1 in 10', V('nursesPer1000', 'THA', 2023) / V('doctorsPer1000', 'THA', 2021) > 6.5 and V('under5Mortality', 'THA', 1990) / L('under5Mortality', 'THA') > 4 and 9.5 < L('diabetesPct', 'THA') < 10.8)

# United Kingdom
gap = U.K('GBR', Y, 'Births') - U.K('GBR', Y, 'Deaths')
C('united-kingdom', 'births exceed deaths by <1,000', 0 < gap < 1000 and f'{gap:,}' in H('united-kingdom'))
C('united-kingdom', 'migrants 4th >17%, net migration >300,000', top('migrantStock', 'GBR') == 4 and L('migrantPct', 'GBR') > 17 and U.K('GBR', Y, 'NetMigrations') > 300e3)
C('united-kingdom', '5th GDP, 4th exporter/importer, services 12th', top('gdp', 'GBR') == 5 and top('exports', 'GBR') == 4 and top('imports', 'GBR') == 4 and top('empSrvPct', 'GBR') == 12)
C('united-kingdom', 'protected 8th (land+sea and sea), wind+solar via Ember (skipped), accounts 4th, tax 9th, articles 5th, women MPs 28th', top('protectedPct', 'GBR') == 8 and top('protectedMarinePct', 'GBR') == 8 and top('accountPct', 'GBR') == 4 and top('taxRevenuePctGdp', 'GBR') == 9 and top('journalArticles', 'GBR') == 5 and top('womenParliamentPct', 'GBR') == 28)
u5 = S('under5Mortality', 'GBR'); C('united-kingdom/health', 'u5 up every year since 2021; newborn above 2015', all(u5[y] > u5[y - 1] for y in range(2022, 2025)) and L('neonatalMortality', 'GBR') > V('neonatalMortality', 'GBR', 2015))
mv = S('measlesVaccPct', 'GBR'); C('united-kingdom/health', 'measles peak 2013–15, now >3 lower', [y for y, v in mv.items() if v == max(mv.values())] == [2013, 2014, 2015] and mv[2024] < mv[2015] - 3)
C('united-kingdom/health', 'tobacco ~1/3 of 2000; doctors >2x 1990; nurses 23rd; health peak 2020, 16th', 0.32 < L('tobaccoPct', 'GBR') / V('tobaccoPct', 'GBR', 2000) < 0.35 and V('doctorsPer1000', 'GBR', 2023) > 2 * V('doctorsPer1000', 'GBR', 1990) and top('nursesPer1000', 'GBR') == 23 and max(S('healthSpendPctGdp', 'GBR'), key=S('healthSpendPctGdp', 'GBR').get) == 2020 and top('healthSpendPctGdp', 'GBR') == 16)

print(', '.join(f'{v} {k}' for k, v in counts.items()))
report()
