# Independent check of the task 170 pages: hub (/country/<slug>/) and health page (/country/<slug>/health/) for
# India, China, United States, Indonesia, Pakistan, Nigeria, Brazil, Russia, Ethiopia and Mexico.
# Reads the ORIGINAL UN WPP / WUP and World Bank files (never src/data/wpp, src/data/wdi or the profiles) and the
# built pages in dist/. Checks:
#   1. every World Bank and UN statistic row on both pages (value, year, world rank) against the original files;
#   2. every cell of the yearly health table against the original World Bank files;
#   3. every number in the JSON-LD (headline, descriptions, FAQ) appears on the page;
#   4. the claims each page makes in its text, recomputed from the original files.
# Energy (Ember / Global Carbon Budget) rows are compared with their originals by check-energy, country facts by
# check-facts; they are only counted here.
#   python3 scripts/verify/batch-170.py   (after npm run build)
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _wdi import wdi, ECON, claim, report, ordn, page_text
import _wdi
import _un as U

COUNTRIES = [('india', 'IND'), ('china', 'CHN'), ('united-states', 'USA'), ('indonesia', 'IDN'), ('pakistan', 'PAK'),
             ('nigeria', 'NGA'), ('brazil', 'BRA'), ('russia', 'RUS'), ('ethiopia', 'ETH'), ('mexico', 'MEX')]
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
    return Decimal(repr(v)).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
fmt = {
    'int': lambda v: f"{hu(v, 0):,}", 'pct': lambda v: f"{hu(v, 1)}%".replace('-0.0%', '0.0%'), 'dec1': lambda v: f"{hu(v, 1)}", 'dec2': lambda v: f"{hu(v, 2)}",
    'usd': _wdi.usd, 'usdWhole': lambda v: f"${round(v):,}", 'intd': lambda v: f"Int${round(v):,}",
}
def rank_wdi(key, iso, year, low, since=None):
    src = W(key); s0 = since or year - 5
    vals = {k: v[max(y for y in v if y >= s0)] for k, v in src.items() if k in ECON and any(y >= s0 for y in v)}
    order = sorted(vals.items(), key=lambda kv: ((kv[1] if low else -kv[1]), kv[0]))
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
                want = f"{ordn(r)} {'lowest' if st['rank'] == 'low' else 'highest'} of {n}"
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

# India
C('india', 'first by population, China second', sorted(pop, key=pop.get, reverse=True)[:2] == ['IND', 'CHN'])
C('india', 'world share 17–18.5%', 17 < pop['IND'] / U.P('WORLD', Y) * 100 < 18.5)
C('india', '6th GDP, outside top 160 per person', top('gdp', 'IND') == 6 and top('gdpPerCapita', 'IND') > 160)
C('india', 'lowest Gini', bottom('gini', 'IND') == 1)
C('india', 'largest remittances', top('remittances', 'IND') == 1)
C('india', 'women participation under 35%, men over 75%, rank > 160', L('lfpFemale', 'IND') < 35 and L('lfpMale', 'IND') > 75 and top('lfpFemale', 'IND') > 160)
C('india', '2nd labour force and mobile subscriptions', top('labourForce', 'IND') == 2 and top('mobileSubs', 'IND') == 2)
C('india', '11th-worst PM2.5', top('pm25', 'IND') == 11)
u5 = S('under5Mortality', 'IND')
C('india/health', 'child deaths down 78–80% since 1990', 78 < (1 - u5[2024] / u5[1990]) * 100 < 80)
C('india/health', 'newborn share 62–64%', 62 < V('neonatalMortality', 'IND', 2024) / u5[2024] * 100 < 64)
m = S('maternalMortality', 'IND'); C('india/health', 'maternal 2021 jump, 2023 below 2020, under a sixth of 1990', m[2021] > 1.5 * m[2020] and m[2023] < m[2020] and m[2023] / m[1990] < 0.16)
o = S('outOfPocketPct', 'IND'); C('india/health', 'out of pocket >70% (2000) to <45%', o[2000] > 70 and o[2023] < 45)
C('india/health', 'more than two nurses per doctor', V('nursesPer1000', 'IND', 2020) > 2 * V('doctorsPer1000', 'IND', 2020))
C('india/health', 'stunting 16th', top('stuntingPct', 'IND') == 16)
h = S('undernourishedPct', 'IND'); C('india/health', 'undernourishment lowest since 2001', min(h) == 2001 and all(v > h[2024] for y, v in h.items() if y != 2024))
tb = S('tbIncidence', 'IND'); C('india/health', 'TB down >40% since 2000, 38th', tb[2024] < 0.6 * tb[2000] and top('tbIncidence', 'IND') == 38)
C('india/health', 'measles 56% (2000) to 97%', V('measlesVaccPct', 'IND', 2000) == 56 and L('measlesVaccPct', 'IND') == 97)

# China
C('china', 'second by population, deaths > births', sorted(pop, key=pop.get, reverse=True)[1] == 'CHN' and U.K('CHN', Y, 'Births') < U.K('CHN', Y, 'Deaths'))
C('china', 'fertility under 1.1', U.f('CHN', Y, 'TFR') < 1.1)
C('china', 'top exporter, 2nd importer, top reserves and container traffic', top('exports', 'CHN') == 1 and top('imports', 'CHN') == 2 and top('reserves', 'CHN') == 1 and top('containerTeu', 'CHN') == 1)
C('china', 'most articles and resident patents', top('journalArticles', 'CHN') == 1 and top('patentsResident', 'CHN') == 1)
C('china', 'GDP 2nd to the US', top('gdp', 'CHN') == 2 and top('gdp', 'USA') == 1)
C('china', 'manufacturing share 9th', top('manufPctGdp', 'CHN') == 9)
u5 = S('under5Mortality', 'CHN'); C('china/health', 'under-five a ninth to a tenth of 1990', 9 < u5[1990] / u5[2024] < 10)
C('china/health', 'newborn >11x, maternal >6x down', V('neonatalMortality', 'CHN', 1990) / V('neonatalMortality', 'CHN', 2024) > 11 and V('maternalMortality', 'CHN', 1990) / V('maternalMortality', 'CHN', 2023) > 6)
C('china/health', 'nurses >4x, doctors >2.7x 1990', V('nursesPer1000', 'CHN', 2022) / V('nursesPer1000', 'CHN', 1990) > 4 and V('doctorsPer1000', 'CHN', 2022) / V('doctorsPer1000', 'CHN', 1990) > 2.7)
C('china/health', 'beds 20th', top('hospitalBedsPer1000', 'CHN') == 20)
C('china/health', 'measles 99% 2010–2022, then 95%', all(v == 99 for y, v in S('measlesVaccPct', 'CHN').items() if 2010 <= y <= 2022) and V('measlesVaccPct', 'CHN', 2023) == 95 and L('measlesVaccPct', 'CHN') == 95)
C('china/health', 'tobacco >20%, down <5 points; diabetes 10.5–12.5%', L('tobaccoPct', 'CHN') > 20 and V('tobaccoPct', 'CHN', 2000) - L('tobaccoPct', 'CHN') < 5 and 10.5 < L('diabetesPct', 'CHN') < 12.5)

# United States
C('united-states', 'most immigrants, >15% of residents, net migration >1 million', top('migrantStock', 'USA') == 1 and L('migrantPct', 'USA') > 15 and U.K('USA', Y, 'NetMigrations') > 1e6)
C('united-states', 'GDP 1st, 11th per person, FDI 1st', top('gdp', 'USA') == 1 and top('gdpPerCapita', 'USA') == 11 and top('fdiInflows', 'USA') == 1)
C('united-states', 'health per person 1st, share 3rd', top('healthSpendPerCapita', 'USA') == 1 and top('healthSpendPctGdp', 'USA') == 3)
C('united-states', 'Gini 20th', top('gini', 'USA') == 20)
C('united-states', 'first for remittances paid, air passengers, tourism receipts, non-resident patents; 5th R&D', all(top(k, 'USA') == 1 for k in ('remittancesPaid', 'airPassengers', 'tourismReceipts', 'patentsNonresident')) and top('rdSpendPctGdp', 'USA') == 5)
u5 = S('under5Mortality', 'USA'); C('united-states/health', 'under-five unchanged at 6.5 since 2018', all(v == 6.5 for y, v in u5.items() if y >= 2018))
C('united-states/health', 'China and Russia below the US', V('under5Mortality', 'CHN', 2024) < u5[2024] and V('under5Mortality', 'RUS', 2024) < u5[2024])
m = S('maternalMortality', 'USA'); C('united-states/health', 'maternal above 1990, peak 2021', m[2023] > m[1990] and max(m, key=m.get) == 2021)
n = S('neonatalMortality', 'USA'); C('united-states/health', 'newborn low 3.5, now higher', min(n.values()) == 3.5 and n[2024] > 3.5)
hg = S('healthSpendPctGdp', 'USA'); C('united-states/health', 'health share peak in 2020', max(hg, key=hg.get) == 2020)
C('united-states/health', 'nurses 8th, >3.5 per doctor', top('nursesPer1000', 'USA') == 8 and V('nursesPer1000', 'USA', 2022) / V('doctorsPer1000', 'USA', 2022) > 3.5)
C('united-states/health', 'tobacco below half of 2000; diabetes 13–15.5%', L('tobaccoPct', 'USA') < V('tobaccoPct', 'USA', 2000) / 2 and 13 < L('diabetesPct', 'USA') < 15.5)

# Indonesia
C('indonesia', '4th population, labour force, mobile subscriptions', sorted(pop, key=pop.get, reverse=True)[3] == 'IDN' and top('labourForce', 'IDN') == 4 and top('mobileSubs', 'IDN') == 4)
C('indonesia', 'over half forest, 8th forest area', L('forestPct', 'IDN') > 50 and top('forestArea', 'IDN') == 8)
C('indonesia', '8th-lowest education spending; literacy >95%', bottom('eduSpendPctGdp', 'IDN') == 8 and L('literacyPct', 'IDN') > 95)
C('indonesia', 'account 50–60%', 50 < L('accountPct', 'IDN') < 60)
C('indonesia', '17th GDP, 19th industry share', top('gdp', 'IDN') == 17 and top('industryPctGdp', 'IDN') == 19)
tb = S('tbIncidence', 'IDN'); C('indonesia/health', 'TB 13th, above 2000 and 2020', top('tbIncidence', 'IDN') == 13 and tb[2024] > tb[2000] and tb[2024] > tb[2020])
mv = S('measlesVaccPct', 'IDN'); C('indonesia/health', 'measles 88 → 72 → 92 → 85', (mv[2019], mv[2021], mv[2022], mv[2024]) == (88, 72, 92, 85))
st_ = S('stuntingPct', 'IDN'); C('indonesia/health', 'stunting roughly halved since 2000', st_[2023] < 0.55 * st_[2000])
C('indonesia/health', 'tobacco 26th, 30–33.4%, down <4 points', top('tobaccoPct', 'IDN') == 26 and 30 < L('tobaccoPct', 'IDN') < 33.4 and V('tobaccoPct', 'IDN', 2000) - L('tobaccoPct', 'IDN') < 4)
C('indonesia/health', '9th-lowest health spending share', bottom('healthSpendPctGdp', 'IDN') == 9)
C('indonesia/health', 'doctors lower in 2023 than 2022', V('doctorsPer1000', 'IDN', 2023) < V('doctorsPer1000', 'IDN', 2022))

# Pakistan
C('pakistan', '5th population, median age <21, fertility >3.4, net emigration >1 million', sorted(pop, key=pop.get, reverse=True)[4] == 'PAK' and U.f('PAK', Y, 'MedianAgePop') < 21 and U.f('PAK', Y, 'TFR') > 3.4 and U.K('PAK', Y, 'NetMigrations') < -1e6)
C('pakistan', '2nd out of school, literacy <60%', top('outOfSchoolPrimary', 'PAK') == 2 and L('literacyPct', 'PAK') < 60)
C('pakistan', "women's accounts 2nd lowest, 11–13%, men >3x", bottom('accountFemalePct', 'PAK') == 2 and 11 < L('accountFemalePct', 'PAK') < 13 and L('accountMalePct', 'PAK') > 3 * L('accountFemalePct', 'PAK'))
C('pakistan', 'water withdrawals >300%, 10th', top('freshwaterWithdrawPct', 'PAK') == 10 and L('freshwaterWithdrawPct', 'PAK') > 300)
C('pakistan', '7th PM2.5, 6th remittances, 1st diabetes', top('pm25', 'PAK') == 7 and top('remittances', 'PAK') == 6 and top('diabetesPct', 'PAK') == 1)
n = S('neonatalMortality', 'PAK'); C('pakistan/health', 'newborn 3rd, 63–66% of under-five, more than half of 1990', top('neonatalMortality', 'PAK') == 3 and 63 < n[2024] / V('under5Mortality', 'PAK', 2024) * 100 < 66 and n[2024] > n[1990] / 2)
h = S('undernourishedPct', 'PAK'); C('pakistan/health', 'undernourishment up >3 points since 2019, 2023 peak since 2010', h[2024] > h[2019] + 3 and max((v, y) for y, v in h.items() if y >= 2010)[1] == 2023)
C('pakistan/health', '6th-lowest share, 10th-lowest per person', bottom('healthSpendPctGdp', 'PAK') == 6 and bottom('healthSpendPerCapita', 'PAK') == 10)
C('pakistan/health', 'fewer nurses than doctors, 12th lowest nurses', V('nursesPer1000', 'PAK', 2021) < V('doctorsPer1000', 'PAK', 2021) and bottom('nursesPer1000', 'PAK') == 12)
# countries with fewer nurses than doctors (latest year since 2018 with both)
docs, nurs = W('doctorsPer1000'), W('nursesPer1000')
fewer = []
for k in ECON:
    ys = [y for y in docs.get(k, {}) if y >= 2018 and y in nurs.get(k, {})]
    if ys and nurs[k][max(ys)] < docs[k][max(ys)]: fewer.append(k)
C('pakistan/health', f'Pakistan one of {len(fewer)} (≤12) with fewer nurses than doctors', 'PAK' in fewer and len(fewer) <= 12 and f'one of only {len(fewer)} countries' in pages[('pakistan', 'health')])
C('pakistan/health', 'tobacco more than halved; measles 50 → 86; stunting 11th', L('tobaccoPct', 'PAK') < V('tobaccoPct', 'PAK', 2000) / 2 and V('measlesVaccPct', 'PAK', 1990) == 50 and L('measlesVaccPct', 'PAK') == 86 and top('stuntingPct', 'PAK') == 11)

# Nigeria
big = sorted((e0(k), k) for k in pop if pop[k] > 100e6)
C('nigeria', 'lowest life expectancy of 100M+ countries, by >7 years', big[0][1] == 'NGA' and big[1][0] - big[0][0] > 7)
C('nigeria', '6th population, median age <19, fertility >4', sorted(pop, key=pop.get, reverse=True)[5] == 'NGA' and U.f('NGA', Y, 'MedianAgePop') < 19 and U.f('NGA', Y, 'TFR') > 4)
C('nigeria', 'births more than twice the US', U.K('NGA', Y, 'Births') > 2 * U.K('USA', Y, 'Births'))
C('nigeria', 'most out of school, 2nd-lowest education spending', top('outOfSchoolPrimary', 'NGA') == 1 and bottom('eduSpendPctGdp', 'NGA') == 2)
C('nigeria', 'electricity <65%, clean cooking <30%', L('electricityAccessPct', 'NGA') < 65 and L('cleanCookingPct', 'NGA') < 30)
C('nigeria', "women's participation 3rd, >80%", top('lfpFemale', 'NGA') == 3 and L('lfpFemale', 'NGA') > 80)
C('nigeria', '10th inflation, 4th PM2.5', top('inflationPct', 'NGA') == 10 and top('pm25', 'NGA') == 4)
C('nigeria/health', 'highest under-five and maternal, 2nd infant and newborn', top('under5Mortality', 'NGA') == 1 and top('maternalMortality', 'NGA') == 1 and top('infantMortality', 'NGA') == 2 and top('neonatalMortality', 'NGA') == 2)
u5 = S('under5Mortality', 'NGA'); C('nigeria/health', 'above 115 since 2015, down <2.5', all(v > 115 for y, v in u5.items() if y >= 2015) and u5[2015] - u5[2024] < 2.5)
C('nigeria/health', 'maternal above three quarters of 1990', V('maternalMortality', 'NGA', 2023) > 0.75 * V('maternalMortality', 'NGA', 1990))
C('nigeria/health', 'measles 12th lowest, <60%', bottom('measlesVaccPct', 'NGA') == 12 and L('measlesVaccPct', 'NGA') < 60)
h = S('undernourishedPct', 'NGA'); ys = sorted(y for y in h if y >= 2015)
C('nigeria/health', 'undernourishment up every year since 2015, >2x 2010', all(h[b] > h[a] for a, b in zip(ys, ys[1:])) and h[2024] > 2 * h[2010])
C('nigeria/health', 'out of pocket 70–75%, 6th; malaria 10th; tobacco lowest', 70 < L('outOfPocketPct', 'NGA') < 75 and top('outOfPocketPct', 'NGA') == 6 and top('malariaIncidence', 'NGA') == 10 and bottom('tobaccoPct', 'NGA') == 1)

# Brazil
C('brazil', '7th population, 5th land area', sorted(pop, key=pop.get, reverse=True)[6] == 'BRA' and top('landArea', 'BRA') == 5)
C('brazil', '2nd forest area after Russia, >58% forest', top('forestArea', 'BRA') == 2 and top('forestArea', 'RUS') == 1 and L('forestPct', 'BRA') > 58)
C('brazil', 'Gini 5th, above 50', top('gini', 'BRA') == 5 and L('gini', 'BRA') > 50)
C('brazil', '11th GDP, 6th FDI, 3rd external debt', top('gdp', 'BRA') == 11 and top('fdiInflows', 'BRA') == 6 and top('externalDebt', 'BRA') == 3)
C('brazil', 'fertility <1.6, urban >88%', U.f('BRA', Y, 'TFR') < 1.6 and float(U.urban('BRA')[Y]) > 88)
m = S('maternalMortality', 'BRA'); C('brazil/health', 'maternal nearly doubled by 2021, 2023 within 3 of 2019', m[2021] / m[2019] > 1.9 and m[2023] - m[2019] < 3)
mv = S('measlesVaccPct', 'BRA'); C('brazil/health', 'measles 99% 2006–2012, 2021 lowest since 1997, 93% now', all(mv[y] == 99 for y in range(2006, 2013)) and mv[2021] == min(v for y, v in mv.items() if y >= 1997) and mv[2024] == 93)
C('brazil/health', 'health share 31st, >9.5%', top('healthSpendPctGdp', 'BRA') == 31 and L('healthSpendPctGdp', 'BRA') > 9.5)
u5 = S('under5Mortality', 'BRA'); C('brazil/health', 'under-five <1/4 of 1990; slow since 2019', u5[2024] < u5[1990] / 4 and u5[2019] - u5[2024] < 1.5)
C('brazil/health', 'tobacco about halved; nurses >2x doctors; diabetes 10–11.5%', L('tobaccoPct', 'BRA') < 0.52 * V('tobaccoPct', 'BRA', 2000) and V('nursesPer1000', 'BRA', 2023) > 2 * V('doctorsPer1000', 'BRA', 2023) and 10 < L('diabetesPct', 'BRA') < 11.5)

# Russia
C('russia', 'largest land and forest, >50% forest', top('landArea', 'RUS') == 1 and top('forestArea', 'RUS') == 1 and L('forestPct', 'RUS') > 50)
C('russia', '9th population, deaths > births, net immigration, 10th migrant stock', sorted(pop, key=pop.get, reverse=True)[8] == 'RUS' and U.K('RUS', Y, 'Births') < U.K('RUS', Y, 'Deaths') and U.K('RUS', Y, 'NetMigrations') > 0 and top('migrantStock', 'RUS') == 10)
C('russia', '18th-lowest unemployment, budget surplus', bottom('unemploymentPct', 'RUS') == 18 and L('budgetBalancePctGdp', 'RUS') > 0)
C('russia', '3rd literacy, 8th GDP', top('literacyPct', 'RUS') == 3 and top('gdp', 'RUS') == 8)
C('russia/health', '8th doctors, 9th beds', top('doctorsPer1000', 'RUS') == 8 and top('hospitalBedsPer1000', 'RUS') == 9)
C('russia/health', 'TB down to about a third of 2000', V('tbIncidence', 'RUS', 2024) < 0.37 * V('tbIncidence', 'RUS', 2000))
C('russia/health', 'tobacco 40th, 25–28%, nearly 40% in 2000', top('tobaccoPct', 'RUS') == 40 and 25 < L('tobaccoPct', 'RUS') < 28 and V('tobaccoPct', 'RUS', 2000) > 39)
C('russia/health', 'below the US; under-five <1/4, maternal <1/6 of 1990', V('under5Mortality', 'RUS', 2024) < V('under5Mortality', 'USA', 2024) and V('under5Mortality', 'RUS', 2024) < V('under5Mortality', 'RUS', 1990) / 4 and V('maternalMortality', 'RUS', 2023) < V('maternalMortality', 'RUS', 1990) / 6)
o = S('outOfPocketPct', 'RUS'); C('russia/health', 'out of pocket >10 points below its peak; peak year on page', o[2023] < max(o.values()) - 10 and f'in {max(o, key=o.get)} and' in pages[('russia', 'health')])
C('russia/health', 'diabetes <6%, rank beyond 160', L('diabetesPct', 'RUS') < 6 and top('diabetesPct', 'RUS') > 160)

# Ethiopia
C('ethiopia', '10th population, growth >2.4%', sorted(pop, key=pop.get, reverse=True)[9] == 'ETH' and U.f('ETH', Y, 'PopGrowthRate') > 2.4)
C('ethiopia', 'electricity <60%, clean cooking <10%', L('electricityAccessPct', 'ETH') < 60 and L('cleanCookingPct', 'ETH') < 10)
C('ethiopia', '6th growth, 13th-lowest GDP per person', top('gdpGrowthPct', 'ETH') == 6 and bottom('gdpPerCapita', 'ETH') == 13)
C('ethiopia', '3rd-lowest revenue, 5th-lowest tax, 2nd-lowest spending', bottom('govRevenuePctGdp', 'ETH') == 3 and bottom('taxRevenuePctGdp', 'ETH') == 5 and bottom('govExpensePctGdp', 'ETH') == 2)
C('ethiopia', 'lowest basic sanitation, <11%', bottom('basicSanitationPct', 'ETH') == 1 and L('basicSanitationPct', 'ETH') < 11)
C('ethiopia', 'urban <25%, farm jobs >60%, 3rd out of school', float(U.urban('ETH')[Y]) < 25 and L('empAgriPct', 'ETH') > 60 and top('outOfSchoolPrimary', 'ETH') == 3)
u5 = S('under5Mortality', 'ETH'); C('ethiopia/health', 'under-five +30% in 2021, back to 2020 level in 2023, lower in 2024', u5[2021] > 1.3 * u5[2020] and u5[2023] == u5[2020] and u5[2024] < u5[2020])
C('ethiopia/health', 'maternal under 1/6.5 of 1990', V('maternalMortality', 'ETH', 1990) / V('maternalMortality', 'ETH', 2023) > 6.5)
C('ethiopia/health', 'doctors 18th lowest, one per 6,900–7,100', bottom('doctorsPer1000', 'ETH') == 18 and 6900 < 1000 / L('doctorsPer1000', 'ETH') < 7100)
C('ethiopia/health', 'TB below 30% of 2000', V('tbIncidence', 'ETH', 2024) < 0.3 * V('tbIncidence', 'ETH', 2000))
C('ethiopia/health', 'stunting down more than a third since 2000', V('stuntingPct', 'ETH', 2019) < 0.65 * V('stuntingPct', 'ETH', 2000))
C('ethiopia/health', 'out of pocket +13 points since 2020; 11th-lowest spending share', V('outOfPocketPct', 'ETH', 2023) > V('outOfPocketPct', 'ETH', 2020) + 13 and bottom('healthSpendPctGdp', 'ETH') == 11)
C('ethiopia/health', 'tobacco 4.5–5.5%; measles 38 → 72', 4.5 < L('tobaccoPct', 'ETH') < 5.5 and V('measlesVaccPct', 'ETH', 1990) == 38 and L('measlesVaccPct', 'ETH') == 72)

# Mexico
C('mexico', '2nd remittances, 3rd tourists, 5th women in parliament (>50%)', top('remittances', 'MEX') == 2 and top('touristArrivals', 'MEX') == 3 and top('womenParliamentPct', 'MEX') == 5 and L('womenParliamentPct', 'MEX') > 50)
C('mexico', '14th GDP, growth <1%, 25th slowest', top('gdp', 'MEX') == 14 and bottom('gdpGrowthPct', 'MEX') == 25 and L('gdpGrowthPct', 'MEX') < 1)
C('mexico', '16th exporter, exports >39% of GDP', top('exports', 'MEX') == 16 and L('exportsPctGdp', 'MEX') > 39)
C('mexico', 'account <55%, men >10 points ahead', L('accountPct', 'MEX') < 55 and L('accountMalePct', 'MEX') - L('accountFemalePct', 'MEX') > 10)
C('mexico', '11th population; urban 78–82%', sorted(pop, key=pop.get, reverse=True)[10] == 'MEX' and 78 < float(U.urban('MEX')[Y]) < 82)
C('mexico/health', 'diabetes 30th, 15.5–17.5%; tobacco below median', top('diabetesPct', 'MEX') == 30 and 15.5 < L('diabetesPct', 'MEX') < 17.5 and top('tobaccoPct', 'MEX') > R('tobaccoPct', 'MEX')[1] / 2)
mv = S('measlesVaccPct', 'MEX'); C('mexico/health', 'measles 73 / 99 / 76 / 80', (mv[2019], mv[2021], mv[2023], mv[2024]) == (73, 99, 76, 80))
m = S('maternalMortality', 'MEX'); C('mexico/health', 'maternal more than doubled in 2021, now below 2019', m[2021] > 2.3 * m[2019] and m[2023] < m[2019])
o = S('outOfPocketPct', 'MEX'); C('mexico/health', 'out of pocket >52% (2000) to 40–42%', o[2000] > 52 and 40 < o[2023] < 42)
C('mexico/health', 'beds 123rd, about one per 1,000; stunting 12–13%', top('hospitalBedsPer1000', 'MEX') == 123 and 0.95 < L('hospitalBedsPer1000', 'MEX') < 1.05 and 12 < L('stuntingPct', 'MEX') < 13)
C('mexico/health', 'under-five less than a third of 1990', V('under5Mortality', 'MEX', 1990) / V('under5Mortality', 'MEX', 2024) > 3.3)

print(', '.join(f'{v} {k}' for k, v in counts.items()))
report()
