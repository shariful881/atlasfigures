# Independent check of the task 175 pages: hub (/country/<slug>/) and health page (/country/<slug>/health/) for
# Poland, Uzbekistan, Mozambique, Malaysia, Ghana, Saudi Arabia, Peru, Madagascar, Côte d'Ivoire and Cameroon.
# Reads the ORIGINAL UN WPP / WUP and World Bank files (never src/data/wpp, src/data/wdi or the profiles) and the
# built pages in dist/. Checks:
#   1. every World Bank and UN statistic row on both pages (value, year, world rank) against the original files;
#   2. every cell of the yearly health table against the original World Bank files;
#   3. every number in the JSON-LD (headline, descriptions, FAQ) appears on the page;
#   4. the claims each page makes in its text, recomputed from the original files.
# Energy (Ember / Global Carbon Budget) rows are compared with their originals by check-energy, country facts by
# check-facts; they are only counted here.
#   python3 scripts/verify/batch-175.py   (after npm run build)
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _wdi import wdi, ECON, claim, report, ordn, page_text
import _wdi
import _un as U

COUNTRIES = [('poland', 'POL'), ('uzbekistan', 'UZB'), ('mozambique', 'MOZ'), ('malaysia', 'MYS'), ('ghana', 'GHA'),
             ('saudi-arabia', 'SAU'), ('peru', 'PER'), ('madagascar', 'MDG'), ('cote-divoire', 'CIV'), ('cameroon', 'CMR')]
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


def s90(key, iso): return {y: v for y, v in S(key, iso).items() if y >= 1990}
def peak(d): return max(d, key=lambda y: (d[y], -y))
def low(d): return min(d, key=lambda y: (d[y], y))
urb = lambda k: float(U.urban(k)[Y])

# Poland
C('poland', 'deaths 1.4-1.5x births; net emigration; shrinking', 1.4 * B('POL') < D('POL') < 1.5 * B('POL') and NM('POL') < 0 and U.f('POL', Y, 'PopGrowthRate') < 0)
C('poland', 'arrivals 2nd (2019); GDP 21st; exports 20th; maternal 5th lowest', top('touristArrivals', 'POL') == 2 and yr('touristArrivals', 'POL') == 2019 and top('gdp', 'POL') == 21 and top('exports', 'POL') == 20 and bottom('maternalMortality', 'POL') == 5)
t = S('tobaccoPct', 'POL')
C('poland/health', 'u5 < 1/4 of 1990; tobacco >40 in 2000, <22, 69th, ratio 0.5-0.6, >18', L('under5Mortality', 'POL') < V('under5Mortality', 'POL', 1990) / 4 and t[2000] > 40 and 18 < L('tobaccoPct', 'POL') < 22 and top('tobaccoPct', 'POL') == 69 and 0.5 < L('tobaccoPct', 'POL') / t[2000] < 0.6)
C('poland/health', 'beds >=6, 16th; doctors 30th; stunting 4th lowest; spending per person 40th', L('hospitalBedsPer1000', 'POL') >= 6 and top('hospitalBedsPer1000', 'POL') == 16 and top('doctorsPer1000', 'POL') == 30 and bottom('stuntingPct', 'POL') == 4 and top('healthSpendPerCapita', 'POL') == 40)

# Uzbekistan
C('uzbekistan', 'births 3.8-4x deaths; remittances >14, 21st; literacy 2nd; primary >100, 10th', 3.8 < B('UZB') / D('UZB') < 4 and L('remittancesPctGdp', 'UZB') > 14 and top('remittancesPctGdp', 'UZB') == 21 and top('literacyPct', 'UZB') == 2 and L('primaryEnrolPct', 'UZB') > 100 and top('primaryEnrolPct', 'UZB') == 10)
C('uzbekistan', 'women MPs 38th; arrivals 30th (2019)', top('womenParliamentPct', 'UZB') == 38 and top('touristArrivals', 'UZB') == 30 and yr('touristArrivals', 'UZB') == 2019)
ms = [v for y, v in S('measlesVaccPct', 'UZB').items() if y >= 1996]; tb = S('tbIncidence', 'UZB')
C('uzbekistan/health', 'u5 < 1/5 of 1990; oop >60, 13th; nurses 19th, 3.8-4 per doctor', L('under5Mortality', 'UZB') < V('under5Mortality', 'UZB', 1990) / 5 and L('outOfPocketPct', 'UZB') > 60 and top('outOfPocketPct', 'UZB') == 13 and top('nursesPer1000', 'UZB') == 19 and 3.8 < L('nursesPer1000', 'UZB') / L('doctorsPer1000', 'UZB') < 4)
C('uzbekistan/health', 'measles 18th, >=95 since 1996; TB peak 2003, < 1/3', top('measlesVaccPct', 'UZB') == 18 and min(ms) >= 95 and peak(tb) == 2003 and L('tbIncidence', 'UZB') < tb[2003] / 3)

# Mozambique
C('mozambique', 'births 5-5.5x deaths; extreme poverty 2nd; GDP per head 5th lowest; debt/GNI 1st >300', 5 < B('MOZ') / D('MOZ') < 5.5 and top('povertyExtremePct', 'MOZ') == 2 and bottom('gdpPerCapita', 'MOZ') == 5 and top('externalDebtPctGni', 'MOZ') == 1 and L('externalDebtPctGni', 'MOZ') > 300)
C('mozambique', 'electricity 10th lowest, 33.4-40; farm jobs 2nd; forest 21st; women MPs 37th', bottom('electricityAccessPct', 'MOZ') == 10 and 33.4 < L('electricityAccessPct', 'MOZ') < 40 and top('empAgriPct', 'MOZ') == 2 and top('forestArea', 'MOZ') == 21 and top('womenParliamentPct', 'MOZ') == 37)
ml = S('malariaIncidence', 'MOZ'); tb = S('tbIncidence', 'MOZ'); m = S('measlesVaccPct', 'MOZ'); u = S('under5Mortality', 'MOZ')
C('mozambique/health', 'u5 1990 >200, now < 1/3.5, one in 16.5-17.5; malaria 8th, peak 2002, <0.65x', u[1990] > 200 and L('under5Mortality', 'MOZ') < u[1990] / 3.5 and 16.5 < 1000 / L('under5Mortality', 'MOZ') < 17.5 and top('malariaIncidence', 'MOZ') == 8 and peak(ml) == 2002 and L('malariaIncidence', 'MOZ') < 0.65 * ml[2002])
C('mozambique/health', 'TB flat since 2012, 18th; measles 17th lowest, 15+ below 2019; doctors 25th lowest; diabetes 5th lowest', all(v == L('tbIncidence', 'MOZ') for y, v in tb.items() if y >= 2012) and tb[2011] < L('tbIncidence', 'MOZ') and top('tbIncidence', 'MOZ') == 18 and bottom('measlesVaccPct', 'MOZ') == 17 and m[2019] - L('measlesVaccPct', 'MOZ') >= 15 and bottom('doctorsPer1000', 'MOZ') == 25 and bottom('diabetesPct', 'MOZ') == 5)

# Malaysia
C('malaysia', 'high-tech >50, 6th; exports/GDP 28th; ports 5th; net immigration; migrants 18th, 10-11%', L('hiTechExportsPct', 'MYS') > 50 and top('hiTechExportsPct', 'MYS') == 6 and top('exportsPctGdp', 'MYS') == 28 and top('containerTeu', 'MYS') == 5 and NM('MYS') > 0 and top('migrantStock', 'MYS') == 18 and 10 < L('migrantPct', 'MYS') < 11)
C('malaysia', 'forest >50; fertiliser 2nd; women MPs 156th; GDP 34th', L('forestPct', 'MYS') > 50 and top('fertiliserKgHa', 'MYS') == 2 and top('womenParliamentPct', 'MYS') == 156 and top('gdp', 'MYS') == 34)
u04 = [v for y, v in S('under5Mortality', 'MYS').items() if y >= 2004]; h = S('healthSpendPctGdp', 'MYS')
C('malaysia/health', 'diabetes >20, 13th, 2011 <12.5; u5 within 0.5 since 2004; health 38th lowest, <4.05, 2000 <2.6; road 57th; stunting 44th', L('diabetesPct', 'MYS') > 20 and top('diabetesPct', 'MYS') == 13 and V('diabetesPct', 'MYS', 2011) < 12.5 and max(u04) - min(u04) < 0.5 and V('under5Mortality', 'MYS', 1990) > 1.9 * L('under5Mortality', 'MYS') and bottom('healthSpendPctGdp', 'MYS') == 38 and L('healthSpendPctGdp', 'MYS') < 4.05 and h[2000] < 2.6 and top('roadDeathsPer100k', 'MYS') == 57 and top('stuntingPct', 'MYS') == 44)

# Ghana
C('ghana', 'births 3.5-3.7x deaths; inflation >14, 14th; urban 55-60; women MPs 150th', 3.5 < B('GHA') / D('GHA') < 3.7 and L('inflationPct', 'GHA') > 14 and top('inflationPct', 'GHA') == 14 and 55 < urb('GHA') < 60 and top('womenParliamentPct', 'GHA') == 150)
ml = S('malariaIncidence', 'GHA'); t = S('tobaccoPct', 'GHA')
C('ghana/health', 'maternal < 1/3 of 1990, 32nd; malaria 25th, peak 2000, < half; tobacco 2nd lowest, < half 2000, one in 29-31', L('maternalMortality', 'GHA') < V('maternalMortality', 'GHA', 1990) / 3 and top('maternalMortality', 'GHA') == 32 and top('malariaIncidence', 'GHA') == 25 and peak(ml) == 2000 and L('malariaIncidence', 'GHA') < ml[2000] / 2 and bottom('tobaccoPct', 'GHA') == 2 and t[2000] > 2 * L('tobaccoPct', 'GHA') and 29 < 100 / L('tobaccoPct', 'GHA') < 31)
C('ghana/health', 'diabetes 4th lowest; health share 16th lowest; 15-16 nurses per doctor', bottom('diabetesPct', 'GHA') == 4 and bottom('healthSpendPctGdp', 'GHA') == 16 and 15 < L('nursesPer1000', 'GHA') / L('doctorsPer1000', 'GHA') < 16)

# Saudi Arabia
C('saudi-arabia', 'migrants 3rd, 40-41%; remittances paid 3rd; PM2.5 2nd; withdrawals >900, 5th; GDP 19th; reserves 8th; land 12th', top('migrantStock', 'SAU') == 3 and 40 < L('migrantPct', 'SAU') < 41 and top('remittancesPaid', 'SAU') == 3 and top('pm25', 'SAU') == 2 and L('freshwaterWithdrawPct', 'SAU') > 900 and top('freshwaterWithdrawPct', 'SAU') == 5 and top('gdp', 'SAU') == 19 and top('reserves', 'SAU') == 8 and top('landArea', 'SAU') == 12)
t = list(S('tobaccoPct', 'SAU').values())
C('saudi-arabia/health', 'road 8th, >2x 2000; diabetes 7th, >20, up since 2011; u5 < 1/7 of 1990; tobacco within 0.5; spending 42nd; maternal 37th lowest', top('roadDeathsPer100k', 'SAU') == 8 and L('roadDeathsPer100k', 'SAU') > 2 * V('roadDeathsPer100k', 'SAU', 2000) and top('diabetesPct', 'SAU') == 7 and L('diabetesPct', 'SAU') > 20 and L('diabetesPct', 'SAU') > V('diabetesPct', 'SAU', 2011) and L('under5Mortality', 'SAU') < V('under5Mortality', 'SAU', 1990) / 7 and max(t) - min(t) < 0.5 and top('healthSpendPerCapita', 'SAU') == 42 and bottom('maternalMortality', 'SAU') == 37)

# Peru
C('peru', 'forest 10th, >50%; urban >85; density <30; tariff 9th lowest <1; women MPs 23rd; migrants 40th', top('forestArea', 'PER') == 10 and L('forestPct', 'PER') > 50 and urb('PER') > 85 and U.f('PER', Y, 'PopDensity') < 30 and bottom('tariffPct', 'PER') == 9 and L('tariffPct', 'PER') < 1 and top('womenParliamentPct', 'PER') == 23 and top('migrantStock', 'PER') == 40)
u = [v for y, v in sorted(S('under5Mortality', 'PER').items()) if y >= 1990]; st_ = S('stuntingPct', 'PER'); tb = S('tbIncidence', 'PER'); dp = S('dptVaccPct', 'PER')
C('peru/health', 'u5 < 1/6 of 1990, falling every year; stunting 0.28-0.33 of 1991; TB low 2017, up, < half 2000, 49th; DPT 48th lowest, below 2019', L('under5Mortality', 'PER') < u[0] / 6 and dec_(u) and 0.28 * st_[1991] < L('stuntingPct', 'PER') < st_[1991] / 3 and low(tb) == 2017 and L('tbIncidence', 'PER') > tb[2017] and L('tbIncidence', 'PER') < tb[2000] / 2 and top('tbIncidence', 'PER') == 49 and bottom('dptVaccPct', 'PER') == 48 and dp[2019] > L('dptVaccPct', 'PER'))

# Madagascar
C('madagascar', "women's participation 1st; men 5th; national poverty 2nd, 72-78; GDP per head 4th lowest", top('lfpFemale', 'MDG') == 1 and top('lfpMale', 'MDG') == 5 and top('povertyNationalPct', 'MDG') == 2 and 72 < L('povertyNationalPct', 'MDG') < 78 and bottom('gdpPerCapita', 'MDG') == 4)
C('madagascar', 'sanitation 5th lowest; water 8th lowest; clean cooking <3; migrant share 5th lowest; arrivals 2020', bottom('basicSanitationPct', 'MDG') == 5 and bottom('basicWaterPct', 'MDG') == 8 and L('cleanCookingPct', 'MDG') < 3 and bottom('migrantPct', 'MDG') == 5 and yr('touristArrivals', 'MDG') == 2020)
un = S('undernourishedPct', 'MDG'); ms = s90('measlesVaccPct', 'MDG')
C('madagascar/health', 'spending per person lowest; share 24th lowest; undernourishment 3rd, low 2011, +14 points', bottom('healthSpendPerCapita', 'MDG') == 1 and bottom('healthSpendPctGdp', 'MDG') == 24 and top('undernourishedPct', 'MDG') == 3 and low(un) == 2011 and L('undernourishedPct', 'MDG') > un[2011] + 14)
C('madagascar/health', 'measles 7th lowest, <50, peak 2007, <0.6x; DPT 9th lowest; nurses 5th lowest; maternal 12th; stunting 8th, ~40', bottom('measlesVaccPct', 'MDG') == 7 and L('measlesVaccPct', 'MDG') < 50 and peak(ms) == 2007 and L('measlesVaccPct', 'MDG') < 0.6 * ms[2007] and bottom('dptVaccPct', 'MDG') == 9 and bottom('nursesPer1000', 'MDG') == 5 and top('maternalMortality', 'MDG') == 12 and top('stuntingPct', 'MDG') == 8 and abs(L('stuntingPct', 'MDG') - 40) < 1.5)

# Côte d'Ivoire
C('cote-divoire', 'migrants 26th, >8%; literacy 9th lowest ~50; mobile 10th >180; farmland 5th; forest <13; inflation 15th lowest', top('migrantStock', 'CIV') == 26 and L('migrantPct', 'CIV') > 8 and bottom('literacyPct', 'CIV') == 9 and abs(L('literacyPct', 'CIV') - 50) < 0.5 and top('mobilePer100', 'CIV') == 10 and L('mobilePer100', 'CIV') > 180 and top('agriLandPct', 'CIV') == 5 and L('forestPct', 'CIV') < 13 and bottom('inflationPct', 'CIV') == 15)
m = s90('maternalMortality', 'CIV'); after = {y: v for y, v in m.items() if y >= 1997}; pk = peak(after); lo = low({y: v for y, v in m.items() if y <= pk}); n = S('neonatalMortality', 'CIV')
C('cote-divoire/health', 'maternal low 1997, peak 2010, now below 1997, 17th; newborn 17th, 0.55-0.6 of 1990; u5 18th, < half 1990; malaria 13th; tobacco 11th lowest', lo == 1997 and pk == 2010 and L('maternalMortality', 'CIV') < m[1997] and top('maternalMortality', 'CIV') == 17 and top('neonatalMortality', 'CIV') == 17 and 0.55 * n[1990] < L('neonatalMortality', 'CIV') < 0.6 * n[1990] and top('under5Mortality', 'CIV') == 18 and L('under5Mortality', 'CIV') < V('under5Mortality', 'CIV', 1990) / 2 and top('malariaIncidence', 'CIV') == 13 and bottom('tobaccoPct', 'CIV') == 11)

# Cameroon
C('cameroon', 'births 4.6-4.9x deaths; tariff 6th; exports/GDP 16th lowest; logistics 9th lowest; PM2.5 10th; women MPs 52nd; forest 33rd', 4.6 < B('CMR') / D('CMR') < 4.9 and top('tariffPct', 'CMR') == 6 and bottom('exportsPctGdp', 'CMR') == 16 and bottom('logisticsIndex', 'CMR') == 9 and top('pm25', 'CMR') == 10 and top('womenParliamentPct', 'CMR') == 52 and top('forestArea', 'CMR') == 33)
u = s90('under5Mortality', 'CMR'); o = S('outOfPocketPct', 'CMR')
C('cameroon/health', 'oop >2/3, 9th, below 2000; u5 peak 1997 above 1990, now < half, 16th; doctors 17th lowest; malaria 15th; tobacco 8th lowest', L('outOfPocketPct', 'CMR') > 200 / 3 and top('outOfPocketPct', 'CMR') == 9 and o[2000] > L('outOfPocketPct', 'CMR') and peak(u) == 1997 and u[1997] > u[1990] and L('under5Mortality', 'CMR') < u[1997] / 2 and top('under5Mortality', 'CMR') == 16 and bottom('doctorsPer1000', 'CMR') == 17 and top('malariaIncidence', 'CMR') == 15 and bottom('tobaccoPct', 'CMR') == 8)

print(', '.join(f'{v} {k}' for k, v in counts.items()))
report()
