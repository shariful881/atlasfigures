# Independent check of the task 174 pages: hub (/country/<slug>/) and health page (/country/<slug>/health/) for
# Algeria, Iraq, Spain, Argentina, Afghanistan, Yemen, Canada, Angola, Ukraine and Morocco.
# Reads the ORIGINAL UN WPP / WUP and World Bank files (never src/data/wpp, src/data/wdi or the profiles) and the
# built pages in dist/. Checks:
#   1. every World Bank and UN statistic row on both pages (value, year, world rank) against the original files;
#   2. every cell of the yearly health table against the original World Bank files;
#   3. every number in the JSON-LD (headline, descriptions, FAQ) appears on the page;
#   4. the claims each page makes in its text, recomputed from the original files.
# Energy (Ember / Global Carbon Budget) rows are compared with their originals by check-energy, country facts by
# check-facts; they are only counted here.
#   python3 scripts/verify/batch-174.py   (after npm run build)
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _wdi import wdi, ECON, claim, report, ordn, page_text
import _wdi
import _un as U

COUNTRIES = [('algeria', 'DZA'), ('iraq', 'IRQ'), ('spain', 'ESP'), ('argentina', 'ARG'), ('afghanistan', 'AFG'),
             ('yemen', 'YEM'), ('canada', 'CAN'), ('angola', 'AGO'), ('ukraine', 'UKR'), ('morocco', 'MAR')]
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

P50 = [k for k in pop if pop[k] > 50e6]
e050 = sorted(P50, key=lambda k: -U.f(k, Y, 'LEx'))
gr50 = sorted(P50, key=lambda k: -U.f(k, Y, 'PopGrowthRate'))
young50 = sorted(P50, key=lambda k: U.f(k, Y, 'MedianAgePop'))


P30 = [k for k in pop if pop[k] > 30e6]
def srt(key, rev=True): return sorted(P30, key=lambda k: (-key(k) if rev else key(k)))
S_ = lambda key, iso: {y: v for y, v in S(key, iso).items()}
def inc(vals): return all(b > a for a, b in zip(vals, vals[1:]))
def dec_(vals): return all(b < a for a, b in zip(vals, vals[1:]))

# Algeria
C('algeria', 'tenth land; forest 14th lowest <1%', top('landArea', 'DZA') == 10 and bottom('forestPct', 'DZA') == 14 and L('forestPct', 'DZA') < 1)
C('algeria', 'external debt ratio 2nd lowest; savings 11th; women 6th lowest <15; women accounts 5th lowest', bottom('externalDebtPctGni', 'DZA') == 2 and top('savingsPctGdp', 'DZA') == 11 and bottom('lfpFemale', 'DZA') == 6 and L('lfpFemale', 'DZA') < 15 and bottom('accountFemalePct', 'DZA') == 5)
C('algeria', 'education spending 5th; industry jobs 11th; births >3.5x deaths; urban 74–78', top('eduSpendPctGdp', 'DZA') == 5 and top('empIndPct', 'DZA') == 11 and B('DZA') > 3.5 * D('DZA') and 74 < float(U.urban('DZA')[Y]) < 78)
C('algeria/health', 'diabetes 26th, 15.5–18.5, >2x 2011', top('diabetesPct', 'DZA') == 26 and 15.5 < L('diabetesPct', 'DZA') < 18.5 and L('diabetesPct', 'DZA') > 2 * V('diabetesPct', 'DZA', 2011))
tobs = [v for y, v in sorted(S('tobaccoPct', 'DZA').items())]
C('algeria/health', 'tobacco never fell between estimates since 2000', all(b >= a for a, b in zip(tobs, tobs[1:])) and tobs[-1] > tobs[0])
o = S('outOfPocketPct', 'DZA'); C('algeria/health', 'oop peak 2022; now >1.7x 2000; 44th', max(o, key=o.get) == 2022 and L('outOfPocketPct', 'DZA') > 1.7 * o[2000] and top('outOfPocketPct', 'DZA') == 44)
m = S('maternalMortality', 'DZA'); C('algeria/health', 'maternal jump 2020; now below 2019 and < 1/3 1990', m[2020] > 1.3 * m[2019] and m[2023] < m[2019] and m[2023] < m[1990] / 3)
ms = S('measlesVaccPct', 'DZA'); C('algeria/health', 'measles <80 2022, >98 2023, lower 2024; u5 < 1/2.3 1990; TB < half 2000', ms[2022] < 80 and ms[2023] > 98 and ms[2024] < ms[2023] and L('under5Mortality', 'DZA') < V('under5Mortality', 'DZA', 1990) / 2.3 and L('tbIncidence', 'DZA') < V('tbIncidence', 'DZA', 2000) / 2)

# Iraq
gap = U.P('DZA', Y) - U.P('IRQ', Y)
C('iraq', 'Algeria ahead by <25,000; Iraq grows faster; gap on page', 0 < gap < 25000 and U.f('IRQ', Y, 'PopGrowthRate') > U.f('DZA', Y, 'PopGrowthRate') and f'{round(gap):,}' in H('iraq'))
C('iraq', 'GDP fell, 6th weakest; industry 9th; tax 2019 2nd lowest <1.5; revenue 19th', L('gdpGrowthPct', 'IRQ') < 0 and bottom('gdpGrowthPct', 'IRQ') == 6 and top('industryPctGdp', 'IRQ') == 9 and max(S('taxRevenuePctGdp', 'IRQ')) == 2019 and bottom('taxRevenuePctGdp', 'IRQ') == 2 and L('taxRevenuePctGdp', 'IRQ') < 1.5 and top('govRevenuePctGdp', 'IRQ') == 19)
C('iraq', 'unemployment 15th; women 3rd lowest <11; PM2.5 13th; FDI <0 5th lowest; withdrawals 17th >100; births >5.5x deaths', top('unemploymentPct', 'IRQ') == 15 and bottom('lfpFemale', 'IRQ') == 3 and L('lfpFemale', 'IRQ') < 11 and top('pm25', 'IRQ') == 13 and L('fdiInflows', 'IRQ') < 0 and bottom('fdiInflows', 'IRQ') == 5 and top('freshwaterWithdrawPct', 'IRQ') == 17 and L('freshwaterWithdrawPct', 'IRQ') > 100 and B('IRQ') > 5.5 * D('IRQ'))
o = S('outOfPocketPct', 'IRQ'); s12 = [v for y, v in o.items() if y >= 2012]
C('iraq/health', 'oop >50 in 10 of 12 years since 2012; peak 2015; 27th', sum(1 for v in s12 if v > 50) == 10 and len(s12) == 12 and max(o, key=o.get) == 2015 and top('outOfPocketPct', 'IRQ') == 27)
u = S('under5Mortality', 'IRQ'); uf = [u[y] for y in sorted(u) if y >= 2000]
C('iraq/health', 'u5 < half 2000, falling every year', L('under5Mortality', 'IRQ') < u[2000] / 2 and dec_(uf))
t = S('tbIncidence', 'IRQ'); C('iraq/health', 'TB peak 2002, low 2020, now between', max(t, key=t.get) == 2002 and min(t, key=t.get) == 2020 and t[min(t, key=t.get)] < t[2024] < t[2002] / 3)
d = S('doctorsPer1000', 'IRQ'); dd = [d[y] for y in sorted(d) if y >= 2018]
C('iraq/health', 'doctors up each year since 2018, record; >2.5 nurses per doctor; road 38th; diabetes 42nd; maternal up from 2022', inc(dd) and d[max(d)] == max(d.values()) and L('nursesPer1000', 'IRQ') > 2.5 * L('doctorsPer1000', 'IRQ') and top('roadDeathsPer100k', 'IRQ') == 38 and top('diabetesPct', 'IRQ') == 42 and V('maternalMortality', 'IRQ', 2023) > V('maternalMortality', 'IRQ', 2022))

# Spain
age30 = srt(lambda k: U.f(k, Y, 'MedianAgePop')); e30 = srt(lambda k: U.f(k, Y, 'LEx'))
C('spain', 'third-oldest >30M after JPN, ITA; fourth life expectancy', age30[:3] == ['JPN', 'ITA', 'ESP'] and e30[:4] == ['JPN', 'KOR', 'ITA', 'ESP'])
C('spain', 'natural decrease > net immigration; shrinking; migrant stock 6th', D('ESP') - B('ESP') > NM('ESP') > 0 and U.f('ESP', Y, 'PopGrowthRate') < 0 and top('migrantStock', 'ESP') == 6)
C('spain', 'GDP 12th; tourists 8th (2020); ports 10th; women MPs 18th; maternal 8th lowest; air 11th; tertiary 13th', top('gdp', 'ESP') == 12 and top('touristArrivals', 'ESP') == 8 and max(S('touristArrivals', 'ESP')) == 2020 and top('containerTeu', 'ESP') == 10 and top('womenParliamentPct', 'ESP') == 18 and bottom('maternalMortality', 'ESP') == 8 and top('airPassengers', 'ESP') == 11 and top('tertiaryEnrolPct', 'ESP') == 13)
C('spain/health', 'newborn 19th lowest; u5 flat since 2017', bottom('neonatalMortality', 'ESP') == 19 and all(v == L('under5Mortality', 'ESP') for y, v in S('under5Mortality', 'ESP').items() if y >= 2017) and V('under5Mortality', 'ESP', 2016) > L('under5Mortality', 'ESP'))
tobs = [v for y, v in sorted(S('tobaccoPct', 'ESP').items())]
h = S('healthSpendPctGdp', 'ESP')
C('spain/health', 'tobacco falls at every estimate; 39th >25; health peak 2020, 1.5+ lower; per person 30th', dec_(tobs) and top('tobaccoPct', 'ESP') == 39 and L('tobaccoPct', 'ESP') > 25 and max(h, key=h.get) == 2020 and h[2023] < h[2020] - 1.5 and top('healthSpendPerCapita', 'ESP') == 30)
C('spain/health', 'doctors >1.35x 2000, 24th; nurses >1.4x doctors; road 16th lowest; TB < 1/3 2000; diabetes 9–11', L('doctorsPer1000', 'ESP') > 1.35 * V('doctorsPer1000', 'ESP', 2000) and top('doctorsPer1000', 'ESP') == 24 and L('nursesPer1000', 'ESP') > 1.4 * L('doctorsPer1000', 'ESP') and bottom('roadDeathsPer100k', 'ESP') == 16 and L('tbIncidence', 'ESP') < V('tbIncidence', 'ESP', 2000) / 3 and 9 < L('diabetesPct', 'ESP') < 11)

# Argentina
urb30 = srt(lambda k: float(U.urban(k)[Y]) if U.urban(k) and Y in U.urban(k) else 0)
C('argentina', 'most urban >30M, over 90%', urb30[0] == 'ARG' and float(U.urban('ARG')[Y]) > 90)
C('argentina', 'inflation 1st (2024) >200; growth >4; land 8th; arable per person 3rd >1 ha', top('inflationPct', 'ARG') == 1 and max(S('inflationPct', 'ARG')) == 2024 and L('inflationPct', 'ARG') > 200 and L('gdpGrowthPct', 'ARG') > 4 and top('landArea', 'ARG') == 8 and top('arableHaPerPerson', 'ARG') == 3 and L('arableHaPerPerson', 'ARG') > 1)
C('argentina', 'ext debt 8th; imports 7th lowest; tertiary 9th; doctors 9th; clean cooking 100; Gini 18th', top('externalDebt', 'ARG') == 8 and bottom('importsPctGdp', 'ARG') == 7 and top('tertiaryEnrolPct', 'ARG') == 9 and top('doctorsPer1000', 'ARG') == 9 and L('cleanCookingPct', 'ARG') == 100 and top('gini', 'ARG') == 18)
t = S('tbIncidence', 'ARG'); t20 = [t[y] for y in sorted(t) if y >= 2020]
C('argentina/health', 'TB low 2010, up every year since 2020, >1.8x low', min(t, key=t.get) == 2010 and inc(t20) and t[2024] > 1.8 * t[2010])
dp = S('dptVaccPct', 'ARG'); C('argentina/health', 'DPT peak 2004, <70 in 2023, 37th lowest; measles <85', max(dp, key=dp.get) == 2004 and dp[2023] < 70 and bottom('dptVaccPct', 'ARG') == 37 and L('measlesVaccPct', 'ARG') < 85)
m = S('maternalMortality', 'ARG'); C('argentina/health', 'maternal ~doubled 2021, now lowest; doctors 9th; health share 26th; diabetes 37th >2.5x 2011; oop 23–27', m[2021] > 1.8 * m[2020] and m[2023] == min(m.values()) and top('healthSpendPctGdp', 'ARG') == 26 and top('diabetesPct', 'ARG') == 37 and L('diabetesPct', 'ARG') > 2.5 * V('diabetesPct', 'ARG', 2011) and 23 < L('outOfPocketPct', 'ARG') < 27)

# Afghanistan
bd30 = srt(lambda k: B(k) / D(k))
C('afghanistan', 'births per death: UGA, YEM, SAU, AFG; >6', bd30[:4] == ['UGA', 'YEM', 'SAU', 'AFG'] and B('AFG') > 6 * D('AFG'))
C('afghanistan', 'GDP per person 2nd lowest; consumption 4th >100; lowest inflation <0', bottom('gdpPerCapita', 'AFG') == 2 and top('householdConsPctGdp', 'AFG') == 4 and L('householdConsPctGdp', 'AFG') > 100 and bottom('inflationPct', 'AFG') == 1 and L('inflationPct', 'AFG') < 0)
C('afghanistan', 'women 2nd lowest after YEM; literacy 4th lowest; accounts 2nd lowest; internet 8th lowest; LPI 2nd lowest; agri 6th', bottom('lfpFemale', 'AFG') == 2 and bottom('lfpFemale', 'YEM') == 1 and bottom('literacyPct', 'AFG') == 4 and bottom('accountPct', 'AFG') == 2 and bottom('internetPct', 'AFG') == 8 and bottom('logisticsIndex', 'AFG') == 2 and top('agriPctGdp', 'AFG') == 6)
C('afghanistan/health', 'maternal 7th, < 1/2.9 1990', top('maternalMortality', 'AFG') == 7 and L('maternalMortality', 'AFG') < V('maternalMortality', 'AFG', 1990) / 2.9)
h = S('healthSpendPctGdp', 'AFG'); C('afghanistan/health', 'health share 4th, peak 2022 >23; oop 4th, 72–78', top('healthSpendPctGdp', 'AFG') == 4 and max(h, key=h.get) == 2022 and h[2022] > 23 and top('outOfPocketPct', 'AFG') == 4 and 72 < L('outOfPocketPct', 'AFG') < 78)
C('afghanistan/health', 'newborn 6th, 30–36; u5 < 1/3 1990; DPT 8th lowest; beds 6th lowest; diabetes >10', top('neonatalMortality', 'AFG') == 6 and 30 < L('neonatalMortality', 'AFG') < 36 and L('under5Mortality', 'AFG') < V('under5Mortality', 'AFG', 1990) / 3 and bottom('dptVaccPct', 'AFG') == 8 and bottom('hospitalBedsPer1000', 'AFG') == 6 and L('diabetesPct', 'AFG') > 10)
un = {y: v for y, v in S('undernourishedPct', 'AFG').items() if y >= 2005}
C('afghanistan/health', 'undernourishment low 2009, 2022 >1.8x, lower now; 12th; stunting 7th', min(un, key=un.get) == 2009 and un[2022] > 1.8 * un[2009] and L('undernourishedPct', 'AFG') < un[2022] and top('undernourishedPct', 'AFG') == 12 and top('stuntingPct', 'AFG') == 7)
ml = S('malariaIncidence', 'AFG'); C('afghanistan/health', 'malaria low 2021, now >2.5x', min(ml, key=ml.get) == 2021 and L('malariaIncidence', 'AFG') > 2.5 * ml[2021])

# Yemen
C('yemen', 'second births per death after UGA, 7–7.5', bd30[:2] == ['UGA', 'YEM'] and 7 * D('YEM') < B('YEM') < 7.5 * D('YEM'))
wp = W('womenParliamentPct'); zero = [k for k in wp if k in pop and wp[k] and wp[k][max(wp[k])] == 0 and max(wp[k]) >= 2020]
C('yemen', 'lowest women participation; one of three parliaments with no women; fewest women accounts', bottom('lfpFemale', 'YEM') == 1 and L('womenParliamentPct', 'YEM') == 0 and len(zero) == 3 and bottom('accountFemalePct', 'YEM') == 1)
C('yemen', 'measles 2nd lowest; stunting 2nd >45; GDP ends 2018; per person 6th lowest; consumption 3rd >100; unemployment 12th; water 14th; PM2.5 15th; urban 34–40', bottom('measlesVaccPct', 'YEM') == 2 and top('stuntingPct', 'YEM') == 2 and L('stuntingPct', 'YEM') > 45 and max(S('gdp', 'YEM')) == 2018 and bottom('gdpPerCapita', 'YEM') == 6 and top('householdConsPctGdp', 'YEM') == 3 and L('householdConsPctGdp', 'YEM') > 100 and top('unemploymentPct', 'YEM') == 12 and top('freshwaterWithdrawPct', 'YEM') == 14 and top('pm25', 'YEM') == 15 and 34 < float(U.urban('YEM')[Y]) < 40)
dp = S('dptVaccPct', 'YEM'); before = [y for y in sorted(dp) if y < 2024 and dp[y] <= dp[2024]]
C('yemen/health', 'DPT 2nd lowest, lowest since 1997, 15+ below 2022', bottom('dptVaccPct', 'YEM') == 2 and before[-1] == 1997 and dp[2022] > dp[2024] + 15)
C('yemen/health', 'stunting up from 2021', L('stuntingPct', 'YEM') > V('stuntingPct', 'YEM', 2021))
ml = S('malariaIncidence', 'YEM'); C('yemen/health', 'malaria low 2015, now >2x', min(ml, key=ml.get) == 2015 and L('malariaIncidence', 'YEM') > 2 * ml[2015])
d = S('doctorsPer1000', 'YEM'); C('yemen/health', 'oop 8th; doctors 12th lowest < 1/3 2004 peak; beds 10th lowest; maternal & u5 < 1/3 1990; road 29th', top('outOfPocketPct', 'YEM') == 8 and bottom('doctorsPer1000', 'YEM') == 12 and max(d, key=d.get) == 2004 and L('doctorsPer1000', 'YEM') < d[2004] / 3 and bottom('hospitalBedsPer1000', 'YEM') == 10 and L('maternalMortality', 'YEM') < V('maternalMortality', 'YEM', 1990) / 3 and L('under5Mortality', 'YEM') < V('under5Mortality', 'YEM', 1990) / 3 and top('roadDeathsPer100k', 'YEM') == 29)

# Canada
nm30 = srt(lambda k: NM(k) / pop[k]); nat = B('CAN') - D('CAN')
C('canada', 'highest net migration rate >30M; net >9x natural; migrants 7th', nm30[0] == 'CAN' and nat > 0 and NM('CAN') > 9 * nat and top('migrantStock', 'CAN') == 7)
C('canada', 'land 4th, forest 3rd, density 11th lowest, arable per person 4th', top('landArea', 'CAN') == 4 and top('forestArea', 'CAN') == 3 and un_rank('densityPerKm2', 'CAN', True)[0] == 11 and top('arableHaPerPerson', 'CAN') == 4)
C('canada', 'GDP 10th; FDI 8th; nurses 18th; health per person 15th; articles 10th; tourists 9th (2019)', top('gdp', 'CAN') == 10 and top('fdiInflows', 'CAN') == 8 and top('nursesPer1000', 'CAN') == 18 and top('healthSpendPerCapita', 'CAN') == 15 and top('journalArticles', 'CAN') == 10 and top('touristArrivals', 'CAN') == 9 and max(S('touristArrivals', 'CAN')) == 2019)
C('canada/health', 'tobacco < 0.4x 2000, 40th lowest', L('tobaccoPct', 'CAN') < 0.4 * V('tobaccoPct', 'CAN', 2000) and bottom('tobaccoPct', 'CAN') == 40)
m = S('maternalMortality', 'CAN'); C('canada/health', 'maternal peak 2020, now lower but above 1990', max(m, key=m.get) == 2020 and m[2020] > m[2023] > m[1990])
u = S('under5Mortality', 'CAN'); t = S('tbIncidence', 'CAN')
C('canada/health', 'health share 14th; oop <16; u5 low from 2017 to 2021, higher now; TB low 2010, >1.2x; nurses >3.5x doctors; road 29th lowest', top('healthSpendPctGdp', 'CAN') == 14 and L('outOfPocketPct', 'CAN') < 16 and min(u, key=lambda y: (u[y], y)) == 2017 and u[2021] == u[2017] and u[2024] > u[2017] and min(t, key=t.get) == 2010 and t[2024] > 1.2 * t[2010] and L('nursesPer1000', 'CAN') > 3.5 * L('doctorsPer1000', 'CAN') and bottom('roadDeathsPer100k', 'CAN') == 29)

# Angola
g30 = srt(lambda k: U.f(k, Y, 'PopGrowthRate'))
C('angola', 'third-fastest growth >30M after COD, SDN; median <17', g30[:3] == ['COD', 'SDN', 'AGO'] and U.f('AGO', Y, 'MedianAgePop') < 17)
C('angola', 'completion 5th lowest <50; out of school 5th >2m; Gini 7th; inflation 11th; imports 3rd lowest', bottom('primaryCompletionPct', 'AGO') == 5 and L('primaryCompletionPct', 'AGO') < 50 and top('outOfSchoolPrimary', 'AGO') == 5 and L('outOfSchoolPrimary', 'AGO') > 2e6 and top('gini', 'AGO') == 7 and top('inflationPct', 'AGO') == 11 and bottom('importsPctGdp', 'AGO') == 3)
C('angola', 'women 15th >70; industry jobs 7th lowest; forest 12th; health share 8th lowest; ptr 9th; urban 68–74', top('lfpFemale', 'AGO') == 15 and L('lfpFemale', 'AGO') > 70 and bottom('empIndPct', 'AGO') == 7 and top('forestArea', 'AGO') == 12 and bottom('healthSpendPctGdp', 'AGO') == 8 and top('pupilTeacherPrimary', 'AGO') == 9 and 68 < float(U.urban('AGO')[Y]) < 74)
t = S('tbIncidence', 'AGO'); ml = S('malariaIncidence', 'AGO')
C('angola/health', 'TB 15th, peak 2007, < 0.75x; malaria low 2012, >1.6x, 16th', top('tbIncidence', 'AGO') == 15 and max(t, key=t.get) == 2007 and t[2024] < 0.75 * t[2007] and min(ml, key=ml.get) == 2012 and L('malariaIncidence', 'AGO') > 1.6 * ml[2012] and top('malariaIncidence', 'AGO') == 16)
C('angola/health', 'u5 and maternal < 1/4 1990; under $100 per person; measles 9th lowest; undernourishment 2001 >3.5x now; one doctor per 3,800–4,300', L('under5Mortality', 'AGO') < V('under5Mortality', 'AGO', 1990) / 4 and L('maternalMortality', 'AGO') < V('maternalMortality', 'AGO', 1990) / 4 and L('healthSpendPerCapita', 'AGO') < 100 and bottom('measlesVaccPct', 'AGO') == 9 and V('undernourishedPct', 'AGO', 2001) > 3.5 * L('undernourishedPct', 'AGO') and 3800 < 1000 / L('doctorsPer1000', 'AGO') < 4300)

# Ukraine
tfr30 = srt(lambda k: U.f(k, Y, 'TFR'), rev=False)
C('ukraine', 'fastest shrinking >30M; 2nd lowest fertility after KOR; deaths >2x births', g30[-1] == 'UKR' and tfr30[:2] == ['KOR', 'UKR'] and D('UKR') > 2 * B('UKR'))
C('ukraine', 'deepest deficit 2024; expense 3rd; ext debt 10th, 7th of GNI >100; inflation 18th', bottom('budgetBalancePctGdp', 'UKR') == 1 and max(S('budgetBalancePctGdp', 'UKR')) == 2024 and top('govExpensePctGdp', 'UKR') == 3 and top('externalDebt', 'UKR') == 10 and top('externalDebtPctGni', 'UKR') == 7 and L('externalDebtPctGni', 'UKR') > 100 and top('inflationPct', 'UKR') == 18)
C('ukraine', 'arable 4th >50; arable per person 5th; Gini 6th lowest; migrants 14th', top('arableLandPct', 'UKR') == 4 and L('arableLandPct', 'UKR') > 50 and top('arableHaPerPerson', 'UKR') == 5 and bottom('gini', 'UKR') == 6 and top('migrantStock', 'UKR') == 14)
dp = S('dptVaccPct', 'UKR'); ms = S('measlesVaccPct', 'UKR')
C('ukraine/health', 'DPT and measles low 2016; DPT >4x, measles >2x', min(dp, key=dp.get) == 2016 and min(ms, key=ms.get) == 2016 and dp[2024] > 4 * dp[2016] and ms[2024] > 2 * ms[2016])
un = S('undernourishedPct', 'UKR'); uu = [un[y] for y in sorted(un) if y >= 2016]
C('ukraine/health', 'undernourishment up every year since 2016, at max, >2.5x 2019', inc(uu) and un[2024] == max(un.values()) and un[2024] > 2.5 * un[2019])
t = S('tbIncidence', 'UKR'); m = S('maternalMortality', 'UKR')
C('ukraine/health', 'tobacco < 0.6x 2000; TB peak 2003 low 2020; beds 15th; health data end 2021; maternal jump 2021, now below 2020', L('tobaccoPct', 'UKR') < 0.6 * V('tobaccoPct', 'UKR', 2000) and max(t, key=t.get) == 2003 and min(t, key=t.get) == 2020 and t[2020] < t[2024] < t[2003] / 2 and top('hospitalBedsPer1000', 'UKR') == 15 and max(S('healthSpendPctGdp', 'UKR')) == 2021 and m[2021] > 1.4 * m[2020] and m[2023] < m[2020])

# Morocco
C('morocco', 'remittances 16th; net emigration; migrant share 15th lowest; national poverty 3rd lowest <4', top('remittances', 'MAR') == 16 and NM('MAR') < 0 and bottom('migrantPct', 'MAR') == 15 and bottom('povertyNationalPct', 'MAR') == 3 and L('povertyNationalPct', 'MAR') < 4)
C('morocco', 'safe sanitation 3rd lowest <10, basic >85; women 12th lowest 18–22; women accounts 20th lowest; ports 19th; primary 16th; fertility 2.1–2.2', bottom('safeSanitationPct', 'MAR') == 3 and L('safeSanitationPct', 'MAR') < 10 and L('basicSanitationPct', 'MAR') > 85 and bottom('lfpFemale', 'MAR') == 12 and 18 < L('lfpFemale', 'MAR') < 22 and bottom('accountFemalePct', 'MAR') == 20 and top('containerTeu', 'MAR') == 19 and top('primaryEnrolPct', 'MAR') == 16 and 2.1 < U.f('MAR', Y, 'TFR') < 2.2)
o = S('outOfPocketPct', 'MAR'); oo = [o[y] for y in sorted(o) if y >= 2010]; h = S('healthSpendPctGdp', 'MAR')
C('morocco/health', 'maternal < 1/7, u5 < 1/5 of 1990; oop peak 2005, falling every year since 2010; health share at max', L('maternalMortality', 'MAR') < V('maternalMortality', 'MAR', 1990) / 7 and L('under5Mortality', 'MAR') < V('under5Mortality', 'MAR', 1990) / 5 and max(o, key=o.get) == 2005 and dec_(oo) and h[2023] == max(h.values()))
C('morocco/health', 'measles >=98 since 2009, 26th; nurses 25th lowest <1; doctors <1; beds 17th lowest; TB 95–100; diabetes >1.7x 2011; tobacco < 0.65x 2000', all(v >= 98 for y, v in S('measlesVaccPct', 'MAR').items() if y >= 2009) and top('measlesVaccPct', 'MAR') == 26 and bottom('nursesPer1000', 'MAR') == 25 and L('nursesPer1000', 'MAR') < 1 and L('doctorsPer1000', 'MAR') < 1 and bottom('hospitalBedsPer1000', 'MAR') == 17 and 95 < L('tbIncidence', 'MAR') < 100 and L('diabetesPct', 'MAR') > 1.7 * V('diabetesPct', 'MAR', 2011) and L('tobaccoPct', 'MAR') < 0.65 * V('tobaccoPct', 'MAR', 2000))

print(', '.join(f'{v} {k}' for k, v in counts.items()))
report()
