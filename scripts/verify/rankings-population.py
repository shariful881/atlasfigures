# Run after `npm run build`: python3 scripts/verify/rankings-population.py
# Independent check of /rankings/population-by-country/ and /rankings/population-density-by-country/ against the
# ORIGINAL UN files (via _un.py, not the site's generated data): every table row, order and value, every CSV row,
# and every figure and claim in the text.
import sys, re, html
sys.path.insert(0, 'scripts/verify')
from _un import *

Y = 2026
REG = {'Africa': {'910','911','912','913','914'}, 'Asia': {'5500','906','920','5501','922'}, 'Europe': {'923','924','925','926'},
       'Latin America and the Caribbean': {'915','916','931'}, 'Northern America': {'918'}, 'Oceania': {'927','928','954','957'}}
K_ = [k for k in raw if k != 'WORLD']
region = lambda k: next(r for r, s in REG.items() if raw[k][Y]['ParentID'] in s)
dens = lambda k, y=Y: f(k, y, 'PopDensity')
bad = 0; n = 0
def chk(ok, what):
    global bad, n
    n += 1; bad += not ok
    if not ok: print('MISS', what)

def page(slug):
    p = open(f'dist/rankings/{slug}/index.html').read()
    text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', p, flags=re.S))))
    rows = re.findall(r'<tr data-iso3="(\w+)" data-rank="(\d+)".*?<span class="n"[^>]*>([^<]+)</span>', p, re.S)
    csv = [l.split(',') for l in open(f'dist/data/{slug}.csv').read().splitlines() if re.match(r'^\d+,', l)]
    return p, text, rows, csv

W = lambda y: P('WORLD', y)
# ---------- population by country ----------
p, text, rows, csv = page('population-by-country')
order = sorted(K_, key=lambda k: -P(k, Y))
chk(len(rows) == len(order) == 237, f'table rows {len(rows)}')
for i, (iso, rk, val) in enumerate(rows):
    chk(iso == order[i] and int(rk) == i + 1 and val == c(P(iso, Y)), f'pop row {i+1} {iso} {val}')
for i, r in enumerate(csv):
    iso = r[2] if not r[1].startswith('"') else re.findall(r',([A-Z]{3}),', ','.join(r))[0]
    chk(iso == order[i] and int(r[0]) == i + 1, f'pop csv row {i+1} {iso}')
    chk(str(P(iso, Y)) in r, f'pop csv value {iso}')
top10 = sum(P(k, Y) for k in order[:10]); cum = 0
for i, k in enumerate(order):
    cum += P(k, Y)
    if cum > W(Y) / 2: half = i + 1; break
regpop = {r: sum(P(k, Y) for k in K_ if region(k) == r) for r in REG}
big1 = [k for k in K_ if P(k, Y) > 1e6]; fast = sorted(big1, key=lambda k: -f(k, Y, 'PopGrowthRate'))
shrink = [k for k in K_ if f(k, Y, 'PopChange') < 0]
o50 = sorted(K_, key=lambda k: -P(k, 2050))
pass_y = next(y for y in range(2010, 2040) if P('IND', y) > P('CHN', y))
wpeak = max(range(1950, 2101), key=lambda y: P('WORLD', y))
small = order[-5:][::-1]
facts = {
  'India 2026': b2(P('IND', Y)), 'China 2026': b2(P('CHN', Y)), 'US 2026': m(P('USA', Y)), 'world': b2(W(Y)),
  'India+China share': p1((P('IND', Y) + P('CHN', Y)) / W(Y) * 100), 'top10 share': p1(top10 / W(Y) * 100), 'half': f'just {half} countries',
  'pass year': f"UN's {pass_y} estimate", 'over 100M': f"{sum(P(k, Y) > 1e8 for k in K_)} countries now have",
  'Asia': p1(regpop['Asia'] / W(Y) * 100), 'Africa': p1(regpop['Africa'] / W(Y) * 100), 'Europe': p1(regpop['Europe'] / W(Y) * 100),
  'LatAm': p1(regpop['Latin America and the Caribbean'] / W(Y) * 100), 'NAm': p1(regpop['Northern America'] / W(Y) * 100), 'Oce': p1(regpop['Oceania'] / W(Y) * 100),
  'CAF growth': f"Central African Republic ({p1(f('CAF', Y, 'PopGrowthRate'))})", 'shrinking': f'{len(shrink)} of the 237', 'MDA': f"Moldova's {p1(f('MDA', Y, 'PopGrowthRate'))}",
  'IND 2050': b2(P('IND', 2050)), 'CHN 2050': b2(P('CHN', 2050)), 'world 2050': b2(W(2050)), 'world peak': f'peaks in {wpeak} at {b2(P("WORLD", wpeak))}',
  'VAT': f'about {c(P("VAT", Y))} residents', 'BGD': f'ranks {ordn(order.index("BGD") + 1)}, home to {m(P("BGD", Y))}',
  'gap': b2(P('IND', Y) - P('CHN', Y)) if P('IND', Y) - P('CHN', Y) >= 1e9 else m(P('IND', Y) - P('CHN', Y)),
}
for k, v in facts.items(): chk(v in text, f'population page: {k} = {v}')
chk([k for k in fast[:4]] == ['CAF', 'SOM', 'NER', 'COD'] and fast[-1] == 'MDA', 'fastest/slowest order')
chk([k for k in o50[:10] if k not in order[:10]] == ['COD'] and [k for k in order[:10] if k not in o50[:10]] == ['RUS'] and o50[3] == 'PAK', '2050 top ten changes')
chk(small[0] == 'VAT' and all(P(k, Y) < 5000 for k in small), 'five smallest below 5,000')

# ---------- population density ----------
p, text, rows, csv = page('population-density-by-country')
order = sorted(K_, key=lambda k: -dens(k))
chk(len(rows) == 237, 'density rows')
for i, (iso, rk, val) in enumerate(rows):
    chk(iso == order[i] and int(rk) == i + 1 and val == c(dens(iso)), f'density row {i+1} {iso} {val}')
for i, r in enumerate(csv):
    iso = re.findall(r',([A-Z]{3}),', ','.join(r))[0]
    chk(iso == order[i] and int(r[0]) == i + 1, f'density csv row {i+1} {iso}')
big10 = [k for k in order if P(k, Y) > 1e7]; big100 = [k for k in order if P(k, Y) > 1e8]; big1 = [k for k in order if P(k, Y) > 1e6]
o1000 = [k for k in order if dens(k) > 1000]
chk(order[:5] == ['MCO', 'MAC', 'SGP', 'HKG', 'GIB'] and len(o1000) == 13 and [k for k in o1000 if P(k, Y) > 1e6] == ['SGP', 'HKG', 'BHR', 'BGD'], 'most crowded')
chk(big10[0] == 'BGD' and dens('BGD') > 2 * dens(big10[1]) and big100[:2] == ['BGD', 'IND'] and len(big100) == 16 and order.index('BGD') == 8, 'Bangladesh')
chk(order[-1] == 'GRL' and sorted(k for k in K_ if dens(k) < 1) == ['FLK', 'GRL'] and big1[-4:] == ['CAN', 'NAM', 'AUS', 'MNG'], 'emptiest')
wd = lambda y: f('WORLD', y, 'PopDensity')
chk(3 < wd(Y) / wd(1950) < 4 and 9 < wd(2050) - wd(Y) < 11.5, 'world density tripled; about ten more by 2050')
facts = {
  'world': f'{c(wd(Y))} people per km²', 'MCO': c(dens('MCO')), 'MAC': f"Macao {c(dens('MAC'))}", 'SGP': f"Singapore {c(dens('SGP'))}", 'HKG': f"Hong Kong {c(dens('HKG'))}",
  'BGD': f"{c(dens('BGD'))} per km²", 'BGD land': f"{c(land('BGD'))} km² of land", 'BGD pop': m(P('BGD', Y)), 'IND': f"second at {c(dens('IND'))}",
  'USA': f"United States has {c(dens('USA'))}", 'RUS': f"Russia {c(dens('RUS'))}", 'MNG': f"emptiest at {c(dens('MNG'))}", 'AUS': f"Australia ({c(dens('AUS'))})",
  'w1950': f"from {c(wd(1950))} per km²", 'w2050': f"({c(wd(2050))})", 'w2100': f"{c(wd(2100))} by 2100",
  'BGD 1950': f"about {c(dens('BGD', 1950))} per km² in 1950", 'BGD 2050': f"{c(dens('BGD', 2050))} projected", 'over1000': f'In all, {len(o1000)} countries',
  'rank': f"{ordn(order.index('BGD') + 1)} on the full list",
}
for k, v in facts.items(): chk(v in text, f'density page: {k} = {v}')
print(f'\nRESULT rankings-population:', 'ALL MATCH' if not bad else f'{bad} mismatches', f'({n} checks)')
sys.exit(bad > 0)
