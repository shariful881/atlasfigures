# Independent check of the task 173 pages: hub (/country/<slug>/) and health page (/country/<slug>/health/) for
# France, South Africa, Tanzania, Italy, Kenya, Myanmar, Colombia, South Korea, Sudan and Uganda.
# Reads the ORIGINAL UN WPP / WUP and World Bank files (never src/data/wpp, src/data/wdi or the profiles) and the
# built pages in dist/. Checks:
#   1. every World Bank and UN statistic row on both pages (value, year, world rank) against the original files;
#   2. every cell of the yearly health table against the original World Bank files;
#   3. every number in the JSON-LD (headline, descriptions, FAQ) appears on the page;
#   4. the claims each page makes in its text, recomputed from the original files.
# Energy (Ember / Global Carbon Budget) rows are compared with their originals by check-energy, country facts by
# check-facts; they are only counted here.
#   python3 scripts/verify/batch-173.py   (after npm run build)
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _wdi import wdi, ECON, claim, report, ordn, page_text
import _wdi
import _un as U

COUNTRIES = [('france', 'FRA'), ('south-africa', 'ZAF'), ('tanzania', 'TZA'), ('italy', 'ITA'), ('kenya', 'KEN'),
             ('myanmar', 'MMR'), ('colombia', 'COL'), ('south-korea', 'KOR'), ('sudan', 'SDN'), ('uganda', 'UGA')]
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


def yr(key, iso): return max(S(key, iso))
def smin(key, iso, since=None):
    s = {y: v for y, v in S(key, iso).items() if since is None or y >= since}; y = min(s, key=lambda k: (s[k], k)); return y, s[y]
def smax(key, iso, since=None):
    s = {y: v for y, v in S(key, iso).items() if since is None or y >= since}; y = max(s, key=lambda k: (s[k], -k)); return y, s[y]
B = lambda k: U.K(k, Y, 'Births'); D = lambda k: U.K(k, Y, 'Deaths'); NM = lambda k: U.K(k, Y, 'NetMigrations')
P50 = [k for k in pop if pop[k] > 50e6]
e050 = sorted(P50, key=lambda k: -U.f(k, Y, 'LEx'))
gr50 = sorted(P50, key=lambda k: -U.f(k, Y, 'PopGrowthRate'))
young50 = sorted(P50, key=lambda k: U.f(k, Y, 'MedianAgePop'))

# France
gap = B('FRA') - D('FRA')
C('france', 'births exceed deaths by <5,000; net migration >20x', 0 < gap < 5000 and NM('FRA') > 20 * gap)
C('france', 'tourists 1st (2020), receipts 3rd; GDP 7th; exports/imports 5th', top('touristArrivals', 'FRA') == 1 and yr('touristArrivals', 'FRA') == 2020 and top('tourismReceipts', 'FRA') == 3 and top('gdp', 'FRA') == 7 and top('exports', 'FRA') == 5 and top('imports', 'FRA') == 5)
C('france', 'migrants 5th, remittances 3rd, expense 9th, broadband 7th, women accounts 1st, marine 7th', top('migrantStock', 'FRA') == 5 and top('remittances', 'FRA') == 3 and top('govExpensePctGdp', 'FRA') == 9 and top('broadbandPer100', 'FRA') == 7 and top('accountFemalePct', 'FRA') == 1 and top('protectedMarinePct', 'FRA') == 7)
C('france/health', 'health share 13th, per person 19th, oop 21st lowest; peak 2021 >0.5 above now', top('healthSpendPctGdp', 'FRA') == 13 and top('healthSpendPerCapita', 'FRA') == 19 and bottom('outOfPocketPct', 'FRA') == 21 and smax('healthSpendPctGdp', 'FRA')[0] == 2021 and L('healthSpendPctGdp', 'FRA') < smax('healthSpendPctGdp', 'FRA')[1] - 0.5)
C('france/health', 'tobacco 18th, down <1.5 since 2000', top('tobaccoPct', 'FRA') == 18 and V('tobaccoPct', 'FRA', 2000) - L('tobaccoPct', 'FRA') < 1.5)
C('france/health', 'newborn low 2010, now +0.4; u5 above 2010', smin('neonatalMortality', 'FRA')[0] == 2010 and L('neonatalMortality', 'FRA') > smin('neonatalMortality', 'FRA')[1] + 0.4 and L('under5Mortality', 'FRA') > V('under5Mortality', 'FRA', 2010))
C('france/health', 'nurses 26th, >2.8 per doctor, beds 19th, measles <75 -> 95', top('nursesPer1000', 'FRA') == 26 and L('nursesPer1000', 'FRA') / L('doctorsPer1000', 'FRA') > 2.8 and top('hospitalBedsPer1000', 'FRA') == 19 and V('measlesVaccPct', 'FRA', 1990) < 75 and L('measlesVaccPct', 'FRA') == 95)

# South Africa
C('south-africa', 'unemployment 2nd >30, youth 2nd >55; Gini 2nd >54; homicide 6th >40', top('unemploymentPct', 'ZAF') == 2 and L('unemploymentPct', 'ZAF') > 30 and top('youthUnemploymentPct', 'ZAF') == 2 and L('youthUnemploymentPct', 'ZAF') > 55 and top('gini', 'ZAF') == 2 and L('gini', 'ZAF') > 54 and top('homicideRate', 'ZAF') == 6 and L('homicideRate', 'ZAF') > 40)
C('south-africa', 'women MPs 16th, tax 10th, mobile 11th, FDI <0 7th lowest, farmland 8th (fossil/CO2 via check-energy)', top('womenParliamentPct', 'ZAF') == 16 and top('taxRevenuePctGdp', 'ZAF') == 10 and top('mobilePer100', 'ZAF') == 11 and L('fdiInflows', 'ZAF') < 0 and bottom('fdiInflows', 'ZAF') == 7 and top('agriLandPct', 'ZAF') == 8)
C('south-africa/health', 'TB peak 2007, < 1/3, 12th', smax('tbIncidence', 'ZAF')[0] == 2007 and L('tbIncidence', 'ZAF') < smax('tbIncidence', 'ZAF')[1] / 3 and top('tbIncidence', 'ZAF') == 12)
C('south-africa/health', 'measles peak 2021, now 10+ lower; DPT <75', smax('measlesVaccPct', 'ZAF')[0] == 2021 and L('measlesVaccPct', 'ZAF') <= smax('measlesVaccPct', 'ZAF')[1] - 10 and L('dptVaccPct', 'ZAF') < 75)
un = S('undernourishedPct', 'ZAF'); C('south-africa/health', 'undernourishment >3x 2004, at highest', L('undernourishedPct', 'ZAF') > 3 * un[2004] and un[max(un)] == max(un.values()))
C('south-africa/health', 'newborn low 2018 now higher; u5 above 2020; u5 2000>1990; oop 11th lowest < half 2000', smin('neonatalMortality', 'ZAF')[0] == 2018 and L('neonatalMortality', 'ZAF') > smin('neonatalMortality', 'ZAF')[1] and L('under5Mortality', 'ZAF') > V('under5Mortality', 'ZAF', 2020) and V('under5Mortality', 'ZAF', 2000) > V('under5Mortality', 'ZAF', 1990) and bottom('outOfPocketPct', 'ZAF') == 11 and L('outOfPocketPct', 'ZAF') < V('outOfPocketPct', 'ZAF', 2000) / 2)
C('south-africa/health', 'maternal 2021 >1.5x now, now <= 2020', V('maternalMortality', 'ZAF', 2021) > 1.5 * L('maternalMortality', 'ZAF') and L('maternalMortality', 'ZAF') <= V('maternalMortality', 'ZAF', 2020))

# Tanzania
C('tanzania', '20th population, births >6x deaths, median <18', rank_pop[19] == 'TZA' and B('TZA') > 6 * D('TZA') and U.f('TZA', Y, 'MedianAgePop') < 18)
C('tanzania', 'women 4th >80, farm jobs 10th, unemployment 12th lowest', top('lfpFemale', 'TZA') == 4 and L('lfpFemale', 'TZA') > 80 and top('empAgriPct', 'TZA') == 10 and bottom('unemploymentPct', 'TZA') == 12)
C('tanzania', 'secondary 6th lowest, tertiary 3rd lowest, ptr 6th, out of school 6th >2m', bottom('secondaryEnrolPct', 'TZA') == 6 and bottom('tertiaryEnrolPct', 'TZA') == 3 and top('pupilTeacherPrimary', 'TZA') == 6 and top('outOfSchoolPrimary', 'TZA') == 6 and L('outOfSchoolPrimary', 'TZA') > 2e6)
C('tanzania', 'protected land 15th, forest area 19th >49%, electricity 17th lowest, services 3rd lowest, savings 18th, women MPs 32nd', top('protectedLandPct', 'TZA') == 15 and top('forestArea', 'TZA') == 19 and L('forestPct', 'TZA') > 49 and bottom('electricityAccessPct', 'TZA') == 17 and bottom('servicesPctGdp', 'TZA') == 3 and top('savingsPctGdp', 'TZA') == 18 and top('womenParliamentPct', 'TZA') == 32)
C('tanzania/health', 'u5 < 1/4.5 of 1990; tobacco < 1/3.5 of 2000, 17th lowest', L('under5Mortality', 'TZA') < V('under5Mortality', 'TZA', 1990) / 4.5 and L('tobaccoPct', 'TZA') < V('tobaccoPct', 'TZA', 2000) / 3.5 and bottom('tobaccoPct', 'TZA') == 17)
C('tanzania/health', 'doctors 14th lowest, spending 15th lowest <$40', bottom('doctorsPer1000', 'TZA') == 14 and bottom('healthSpendPerCapita', 'TZA') == 15 and L('healthSpendPerCapita', 'TZA') < 40)
C('tanzania/health', 'malaria peak 2000, < half, 30th', smax('malariaIncidence', 'TZA')[0] == 2000 and L('malariaIncidence', 'TZA') < smax('malariaIncidence', 'TZA')[1] / 2 and top('malariaIncidence', 'TZA') == 30)
C('tanzania/health', 'undernourishment 27th, -14 since 2002; stunting -19 since 1991; road 20th >30', top('undernourishedPct', 'TZA') == 27 and L('undernourishedPct', 'TZA') < V('undernourishedPct', 'TZA', 2002) - 14 and L('stuntingPct', 'TZA') < V('stuntingPct', 'TZA', 1991) - 19 and top('roadDeathsPer100k', 'TZA') == 20 and L('roadDeathsPer100k', 'TZA') > 30)

# Italy
age50x = sorted(P50, key=lambda k: -U.f(k, Y, 'MedianAgePop'))
C('italy', 'second-oldest >50M after Japan; third life expectancy after JPN, KOR', age50x[:2] == ['JPN', 'ITA'] and e050[:3] == ['JPN', 'KOR', 'ITA'])
r = D('ITA') / B('ITA')
C('italy', 'natural decrease >3x net migration; deaths 1.7–1.8x births; shrinking; fertility <1.25', D('ITA') - B('ITA') > 3 * NM('ITA') and 1.7 < r < 1.8 and U.f('ITA', Y, 'PopGrowthRate') < 0 and U.f('ITA', Y, 'TFR') < 1.25)
C('italy', 'GDP 9th, growth 24th weakest <1, reserves 10th, tourists 6th & receipts 7th (2020)', top('gdp', 'ITA') == 9 and bottom('gdpGrowthPct', 'ITA') == 24 and L('gdpGrowthPct', 'ITA') < 1 and top('reserves', 'ITA') == 10 and top('touristArrivals', 'ITA') == 6 and yr('touristArrivals', 'ITA') == 2020 and top('tourismReceipts', 'ITA') == 7)
C('italy', 'articles 8th, homicide 15th lowest, expense 8th', top('journalArticles', 'ITA') == 8 and bottom('homicideRate', 'ITA') == 15 and top('govExpensePctGdp', 'ITA') == 8)
C('italy/health', 'u5 14th lowest, newborn 22nd, infant 16th; u5 lowest now, < 1/3.5 1990', bottom('under5Mortality', 'ITA') == 14 and bottom('neonatalMortality', 'ITA') == 22 and bottom('infantMortality', 'ITA') == 16 and smin('under5Mortality', 'ITA')[0] == yr('under5Mortality', 'ITA') and L('under5Mortality', 'ITA') < V('under5Mortality', 'ITA', 1990) / 3.5)
C('italy/health', 'measles <45 -> >=95; health peak 2020 >1 above now; doctors 26th >4, <1.7 nurses per doctor; per person 27th', V('measlesVaccPct', 'ITA', 1990) < 45 and L('measlesVaccPct', 'ITA') >= 95 and smax('healthSpendPctGdp', 'ITA')[0] == 2020 and L('healthSpendPctGdp', 'ITA') < smax('healthSpendPctGdp', 'ITA')[1] - 1 and top('doctorsPer1000', 'ITA') == 26 and L('doctorsPer1000', 'ITA') > 4 and L('nursesPer1000', 'ITA') / L('doctorsPer1000', 'ITA') < 1.7 and top('healthSpendPerCapita', 'ITA') == 27)
mm = S('maternalMortality', 'ITA'); C('italy/health', 'oop >20, tobacco -3 since 2000; maternal 2022 above now, now lowest', L('outOfPocketPct', 'ITA') > 20 and L('tobaccoPct', 'ITA') < V('tobaccoPct', 'ITA', 2000) - 3 and mm[2022] > L('maternalMortality', 'ITA') and L('maternalMortality', 'ITA') == min(mm.values()))

# Kenya
C('kenya', 'accounts 36th >90, internet <36; budget 6th deepest < -9.9; poverty 12th >45; remittances 43rd', top('accountPct', 'KEN') == 36 and L('accountPct', 'KEN') > 90 and L('internetPct', 'KEN') < 36 and bottom('budgetBalancePctGdp', 'KEN') == 6 and L('budgetBalancePctGdp', 'KEN') < -9.9 and top('povertyExtremePct', 'KEN') == 12 and L('povertyExtremePct', 'KEN') > 45 and top('remittances', 'KEN') == 43)
C('kenya', 'tariffs 26th, women 29th, men ahead on accounts (renewables via check-energy)', top('tariffPct', 'KEN') == 26 and top('lfpFemale', 'KEN') == 29 and L('accountMalePct', 'KEN') > L('accountFemalePct', 'KEN'))
C('kenya/health', 'undernourishment low 2013, +15 now, 8th; stunting < half 2000', smin('undernourishedPct', 'KEN')[0] == 2013 and top('undernourishedPct', 'KEN') == 8 and L('undernourishedPct', 'KEN') > smin('undernourishedPct', 'KEN')[1] + 15 and L('stuntingPct', 'KEN') < V('stuntingPct', 'KEN', 2000) / 2)
C('kenya/health', 'TB peak 2006 now < 1/3; diabetes 7th lowest; tobacco < half; maternal < 1/3.5, u5 < 1/2.5 of 1990; malaria 36th; oop < 2000/1.9', smax('tbIncidence', 'KEN')[0] == 2006 and L('tbIncidence', 'KEN') < smax('tbIncidence', 'KEN')[1] / 3 and bottom('diabetesPct', 'KEN') == 7 and L('tobaccoPct', 'KEN') < V('tobaccoPct', 'KEN', 2000) / 2 and L('maternalMortality', 'KEN') < V('maternalMortality', 'KEN', 1990) / 3.5 and L('under5Mortality', 'KEN') < V('under5Mortality', 'KEN', 1990) / 2.5 and top('malariaIncidence', 'KEN') == 36 and L('outOfPocketPct', 'KEN') < V('outOfPocketPct', 'KEN', 2000) / 1.9)

# Myanmar
C('myanmar', 'GDP fell, 8th weakest; tax 2019 6th lowest <7; manufacturing 8th >25; farm jobs >44', L('gdpGrowthPct', 'MMR') < 0 and bottom('gdpGrowthPct', 'MMR') == 8 and yr('taxRevenuePctGdp', 'MMR') == 2019 and bottom('taxRevenuePctGdp', 'MMR') == 6 and L('taxRevenuePctGdp', 'MMR') < 7 and top('manufPctGdp', 'MMR') == 8 and L('manufPctGdp', 'MMR') > 25 and L('empAgriPct', 'MMR') > 44)
C('myanmar', 'migrant share 4th lowest, net emigration; R&D 3rd lowest, tariffs 10th lowest, armed 14th, ext debt ratio 9th lowest', bottom('migrantPct', 'MMR') == 4 and NM('MMR') < 0 and bottom('rdSpendPctGdp', 'MMR') == 3 and bottom('tariffPct', 'MMR') == 10 and top('armedForces', 'MMR') == 14 and bottom('externalDebtPctGni', 'MMR') == 9)
mv = S('measlesVaccPct', 'MMR')
C('myanmar/health', 'tobacco 3rd >40, -20 since 2000; measles >90 (2020), <45 (2021), DPT 2021 <40, now 15+ below 2020', top('tobaccoPct', 'MMR') == 3 and L('tobaccoPct', 'MMR') > 40 and L('tobaccoPct', 'MMR') < V('tobaccoPct', 'MMR', 2000) - 20 and mv[2020] > 90 and mv[2021] < 45 and V('dptVaccPct', 'MMR', 2021) < 40 and L('measlesVaccPct', 'MMR') < mv[2020] - 15)
C('myanmar/health', 'TB low 2020, >1.5x now, 7th; malaria >8x 2019 low; oop 7th >70; u5 and maternal < 1/3 1990', smin('tbIncidence', 'MMR')[0] == 2020 and L('tbIncidence', 'MMR') > 1.5 * smin('tbIncidence', 'MMR')[1] and top('tbIncidence', 'MMR') == 7 and smin('malariaIncidence', 'MMR')[0] == 2019 and L('malariaIncidence', 'MMR') > 8 * smin('malariaIncidence', 'MMR')[1] and top('outOfPocketPct', 'MMR') == 7 and L('outOfPocketPct', 'MMR') > 70 and L('under5Mortality', 'MMR') < V('under5Mortality', 'MMR', 1990) / 3 and L('maternalMortality', 'MMR') < V('maternalMortality', 'MMR', 1990) / 3)

# Colombia
C('colombia', 'Gini 1st >54; births >2x deaths, net migration >100k, fertility <2.1, migrants 22nd', top('gini', 'COL') == 1 and L('gini', 'COL') > 54 and B('COL') > 2 * D('COL') and NM('COL') > 100000 and U.f('COL', Y, 'TFR') < 2.1 and top('migrantStock', 'COL') == 22)
C('colombia', 'forest >50, 13th area, marine 12th; ext debt 9th, homicide 15th, mobile 15th, fertiliser 12th, remittances 17th', L('forestPct', 'COL') > 50 and top('forestArea', 'COL') == 13 and top('protectedMarinePct', 'COL') == 12 and top('externalDebt', 'COL') == 9 and top('homicideRate', 'COL') == 15 and top('mobilePer100', 'COL') == 15 and top('fertiliserKgHa', 'COL') == 12 and top('remittances', 'COL') == 17)
tbc = S('tbIncidence', 'COL'); tys = [y for y in sorted(tbc) if y >= 2018]
C('colombia/health', 'maternal peak 2021 >2x now, now lowest; TB up every year since 2018, >1.4x 2015', smax('maternalMortality', 'COL')[0] == 2021 and L('maternalMortality', 'COL') == min(S('maternalMortality', 'COL').values()) and smax('maternalMortality', 'COL')[1] > 2 * L('maternalMortality', 'COL') and all(tbc[b] > tbc[a] for a, b in zip(tys, tys[1:])) and L('tbIncidence', 'COL') > 1.4 * tbc[2015])
C('colombia/health', 'malaria low 2014, >2.5x now; doctors >3x 1990, fewer nurses than doctors; u5 < 1/3 1990; tobacco <0.6x 2000, 19th lowest', smin('malariaIncidence', 'COL')[0] == 2014 and L('malariaIncidence', 'COL') > 2.5 * smin('malariaIncidence', 'COL')[1] and L('doctorsPer1000', 'COL') > 3 * V('doctorsPer1000', 'COL', 1990) and L('nursesPer1000', 'COL') < L('doctorsPer1000', 'COL') and L('under5Mortality', 'COL') < V('under5Mortality', 'COL', 1990) / 3 and L('tobaccoPct', 'COL') < 0.6 * V('tobaccoPct', 'COL', 2000) and bottom('tobaccoPct', 'COL') == 19)

# South Korea
lower = sorted(k for k in pop if U.f(k, Y, 'TFR') < U.f('KOR', Y, 'TFR'))
tfr50 = sorted(P50, key=lambda k: U.f(k, Y, 'TFR'))
C('south-korea', 'only HKG and MAC lower fertility; lowest of >50M; deaths >1.5x births; life expectancy 2nd after JPN', lower == ['HKG', 'MAC'] and tfr50[0] == 'KOR' and D('KOR') > 1.5 * B('KOR') and e050[:2] == ['JPN', 'KOR'])
C('south-korea', 'R&D 3rd, patents 4th, tertiary 5th >100; manufacturing 7th, ports 4th; homicide 10th lowest, broadband 8th, reserves 9th, high-tech 13th', top('rdSpendPctGdp', 'KOR') == 3 and top('patentsResident', 'KOR') == 4 and top('tertiaryEnrolPct', 'KOR') == 5 and L('tertiaryEnrolPct', 'KOR') > 100 and top('manufPctGdp', 'KOR') == 7 and top('containerTeu', 'KOR') == 4 and bottom('homicideRate', 'KOR') == 10 and top('broadbandPer100', 'KOR') == 8 and top('reserves', 'KOR') == 9 and top('hiTechExportsPct', 'KOR') == 13)
C('south-korea/health', 'beds 1st >12; newborn 9th lowest; stunting 2nd lowest <1; tobacco 0.5–0.55x 2000', top('hospitalBedsPer1000', 'KOR') == 1 and L('hospitalBedsPer1000', 'KOR') > 12 and bottom('neonatalMortality', 'KOR') == 9 and bottom('stuntingPct', 'KOR') == 2 and L('stuntingPct', 'KOR') < 1 and 0.5 * V('tobaccoPct', 'KOR', 2000) < L('tobaccoPct', 'KOR') < 0.55 * V('tobaccoPct', 'KOR', 2000))
C('south-korea/health', 'health share >2.3x 2000, nurses >3x 2000, doctors >3x 1990; TB peak 2011 now < peak/2.5; maternal 18th lowest; oop >30, 9+ below 2000', L('healthSpendPctGdp', 'KOR') > 2.3 * V('healthSpendPctGdp', 'KOR', 2000) and L('nursesPer1000', 'KOR') > 3 * V('nursesPer1000', 'KOR', 2000) and L('doctorsPer1000', 'KOR') > 3 * V('doctorsPer1000', 'KOR', 1990) and smax('tbIncidence', 'KOR')[0] == 2011 and L('tbIncidence', 'KOR') < smax('tbIncidence', 'KOR')[1] / 2.5 and bottom('maternalMortality', 'KOR') == 18 and 30 < L('outOfPocketPct', 'KOR') < V('outOfPocketPct', 'KOR', 2000) - 9)

# Sudan
C('sudan', 'second-fastest growth >50M after COD; median <19', gr50[:2] == ['COD', 'SDN'] and U.f('SDN', Y, 'MedianAgePop') < 19)
C('sudan', 'inflation 2022 2nd >100; out of school 2019 4th >3m; primary enrolment 5th lowest; women 7th lowest <15', yr('inflationPct', 'SDN') == 2022 and top('inflationPct', 'SDN') == 2 and L('inflationPct', 'SDN') > 100 and yr('outOfSchoolPrimary', 'SDN') == 2019 and top('outOfSchoolPrimary', 'SDN') == 4 and L('outOfSchoolPrimary', 'SDN') > 3e6 and bottom('primaryEnrolPct', 'SDN') == 5 and bottom('lfpFemale', 'SDN') == 7 and L('lfpFemale', 'SDN') < 15)
C('sudan', 'water 7th >600; cereal 5th lowest; GNI PPP 9th lowest; savings 6th lowest', top('freshwaterWithdrawPct', 'SDN') == 7 and L('freshwaterWithdrawPct', 'SDN') > 600 and bottom('cerealYield', 'SDN') == 5 and bottom('gniPerCapitaPpp', 'SDN') == 9 and bottom('savingsPctGdp', 'SDN') == 6)
u5s = S('under5Mortality', 'SDN')
C('sudan/health', 'DPT lowest <40; measles 6th lowest, 30+ below 2022', bottom('dptVaccPct', 'SDN') == 1 and L('dptVaccPct', 'SDN') < 40 and bottom('measlesVaccPct', 'SDN') == 6 and L('measlesVaccPct', 'SDN') < V('measlesVaccPct', 'SDN', 2022) - 30)
C('sudan/health', 'u5 fell every year 2006–2022, +20% 2023, still above 2022, 20th', all(u5s[y] < u5s[y - 1] for y in range(2007, 2023)) and u5s[2023] > 1.2 * u5s[2022] and L('under5Mortality', 'SDN') > u5s[2022] and top('under5Mortality', 'SDN') == 20)
C('sudan/health', 'spending 2nd lowest <$25, oop >55; malaria at peak, >3x 2011; diabetes 24th >2x 2011; TB < 1/3 2000; maternal < 1/3 1990', bottom('healthSpendPerCapita', 'SDN') == 2 and L('healthSpendPerCapita', 'SDN') < 25 and L('outOfPocketPct', 'SDN') > 55 and smax('malariaIncidence', 'SDN')[0] == yr('malariaIncidence', 'SDN') and L('malariaIncidence', 'SDN') > 3 * V('malariaIncidence', 'SDN', 2011) and top('diabetesPct', 'SDN') == 24 and L('diabetesPct', 'SDN') > 2 * V('diabetesPct', 'SDN', 2011) and L('tbIncidence', 'SDN') < V('tbIncidence', 'SDN', 2000) / 3 and L('maternalMortality', 'SDN') < V('maternalMortality', 'SDN', 1990) / 3)

# Uganda
ratio50 = sorted(P50, key=lambda k: -B(k) / D(k))
C('uganda', 'most births per death >50M (>7), second youngest after COD', ratio50[0] == 'UGA' and B('UGA') / D('UGA') > 7 and young50[:2] == ['COD', 'UGA'])
C('uganda', 'poverty 9th >50; farm jobs 9th, industry jobs 8th lowest, women 9th, farmland 7th, arable 11th', top('povertyExtremePct', 'UGA') == 9 and L('povertyExtremePct', 'UGA') > 50 and top('empAgriPct', 'UGA') == 9 and bottom('empIndPct', 'UGA') == 8 and top('lfpFemale', 'UGA') == 9 and top('agriLandPct', 'UGA') == 7 and top('arableLandPct', 'UGA') == 11)
C('uganda', 'internet 3rd lowest <10, clean cooking 5th lowest, growth 28th (hydro, CO2 per person via check-energy)', bottom('internetPct', 'UGA') == 3 and L('internetPct', 'UGA') < 10 and bottom('cleanCookingPct', 'UGA') == 5 and top('gdpGrowthPct', 'UGA') == 28)
C('uganda/health', 'malaria 14th, peak 2001, now <0.55x; diabetes 3rd lowest <2.5; oop 30–34', top('malariaIncidence', 'UGA') == 14 and smax('malariaIncidence', 'UGA')[0] == 2001 and L('malariaIncidence', 'UGA') < 0.55 * smax('malariaIncidence', 'UGA')[1] and bottom('diabetesPct', 'UGA') == 3 and L('diabetesPct', 'UGA') < 2.5 and 30 < L('outOfPocketPct', 'UGA') < 34)
C('uganda/health', 'u5 < 1/3.5 1990; tobacco < 1/3 2000; DPT <50 -> >90; doctors 28th lowest; undernourishment peak 2017, 15+ lower', L('under5Mortality', 'UGA') < V('under5Mortality', 'UGA', 1990) / 3.5 and L('tobaccoPct', 'UGA') < V('tobaccoPct', 'UGA', 2000) / 3 and V('dptVaccPct', 'UGA', 1990) < 50 and L('dptVaccPct', 'UGA') > 90 and bottom('doctorsPer1000', 'UGA') == 28 and smax('undernourishedPct', 'UGA')[0] == 2017 and L('undernourishedPct', 'UGA') < smax('undernourishedPct', 'UGA')[1] - 15)

print(', '.join(f'{v} {k}' for k, v in counts.items()))
report()
