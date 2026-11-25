# Run after `npm run build`: python3 scripts/verify/world.py
# Independent check of every figure on /population/world/ against the ORIGINAL UN files (via _un.py, not the
# site's generated data): key facts, live counter, table and CSV rows, and every figure and claim in the text.
import sys, re, html, json
sys.path.insert(0, 'scripts/verify')
from _un import *
import _un
_un_rows = lambda: _un._rows; _h = _un._h

Y = 2026; R = range(1950, 2101); EST = range(1950, 2024)
F = lambda y, col: f('WORLD', y, col)
REG_AF = {'910','911','912','913','914'}
K_ = [k for k in raw if k != 'WORLD']
page = open('dist/population/world/index.html').read()
text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S))))
ld = html.unescape(' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)))
yrs = json.load(open('src/data/pages/world.json'))['tableYears']
# World row of the WUP file: LocID 900 (column 4), no ISO3
_row = [r for r in _un_rows() if r[3] == 900][0]
U = {int(_h[i]): _row[i] for i in range(10, len(_h)) if _h[i] and str(_h[i]).isdigit()}
bad = 0; n = 0
def chk(ok, what):
    global bad, n
    n += 1; bad += not ok
    print('OK  ' if ok else 'MISS', what)

gtop = max(R, key=lambda y: F(y, 'PopGrowthRate')); addtop = max(R, key=lambda y: F(y, 'PopChange'))
peak = max(R, key=lambda y: P('WORLD', y)); btop = max(EST, key=lambda y: F(y, 'Births'))
first = lambda v: next(y for y in R if P('WORLD', y) >= v)
ttop = max(R, key=lambda y: F(y, 'TFR')); below = next(y for y in R if F(y, 'TFR') < 2.1)
ch = sorted(K_, key=lambda k: -K(k, Y, 'PopChange'))
le_low = min(range(2019, 2024), key=lambda y: F(y, 'LEx'))
af = lambda y: sum(P(k, y) for k in K_ if raw[k][Y]['ParentID'] in REG_AF) / P('WORLD', y) * 100
day = lambda v: c(round(v / 365))
chk(gtop == 1963 and F(Y, 'PopGrowthRate') * 2.5 < F(gtop, 'PopGrowthRate'), 'growth 1963 peak; now under 1/2.5')
chk(addtop == 1990 and peak == 2084 and P('WORLD', 2100) < P('WORLD', peak), 'largest addition 1990; peak 2084')
chk((first(8e9), first(9e9), first(10e9)) == (2022, 2037, 2061), 'billion milestones')
chk(btop == 2012 and ttop == 1963 and below == 2050, 'births peak 2012; fertility 1963 high, under 2.1 from 2050')
chk(ch[:5] == ['IND', 'NGA', 'PAK', 'COD', 'ETH'] and ch[-1] == 'CHN' and ch[-2] == 'JPN', 'adders and losers')
chk(le_low == 2021 and F(Y, 'LEx') > F(2019, 'LEx'), 'life expectancy dip to 2021, recovered')
chk(3.2 < P('WORLD', Y) / P('WORLD', 1950) < 3.4 and af(1950) < 10 and af(2100) > 37, 'three times 1950; Africa shares')
exp = {
  'population': c(P('WORLD', Y)), 'billions': b2(P('WORLD', Y)), 'growth': p1(F(Y, 'PopGrowthRate')), 'change': c(K('WORLD', Y, 'PopChange')),
  'per day': day(K('WORLD', Y, 'PopChange')), 'births/day': day(K('WORLD', Y, 'Births')), 'deaths/day': day(K('WORLD', Y, 'Deaths')),
  'density': c(F(Y, 'PopDensity')), 'median': f"{F(Y,'MedianAgePop'):.1f}", 'tfr': f"{F(Y,'TFR'):.2f}", 'LE': f"{F(Y,'LEx'):.1f}", 'urban': p1(U[Y]), 'urban 1950': p1(U[1950]),
  'countries': str(len(K_)), 'g peak': f"{gtop} peak of {p1(F(gtop,'PopGrowthRate'))}", 'add top': f"about {m(K('WORLD', addtop, 'PopChange'))}, came in {addtop}",
  'change m': f"about {m(K('WORLD', Y, 'PopChange'))}", 'pop 1950': b2(P('WORLD', 1950)), 'births top': f"about {m(K('WORLD', btop, 'Births'))}, were born in {btop}",
  'births now': f"about {m(K('WORLD', Y, 'Births'))}", 'peak': f"reaches about {b2(P('WORLD', peak))}", 'tfr top': f"{F(ttop,'TFR'):.2f} at the {ttop} high",
  'below': f"2.1 from {below}", 'pop 2100': b2(P('WORLD', 2100)), 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
  'IND': f"about {m(K('IND', Y, 'PopChange'))}, Nigeria's {m(K('NGA', Y, 'PopChange'))}, Pakistan's {m(K('PAK', Y, 'PopChange'))}, DR Congo's {m(K('COD', Y, 'PopChange'))} and Ethiopia's {m(K('ETH', Y, 'PopChange'))}",
  'CHN': f"China loses about {m(-K('CHN', Y, 'PopChange'))} and Japan about {k1(-K('JPN', Y, 'PopChange'))}",
  'Africa': f"{p1(af(1950))} in 1950, is {p1(af(Y))} now and {p1(af(2100))}", 'LE 1950': f"{F(1950,'LEx'):.1f} years in 1950", 'LE dip': f"{F(2019,'LEx'):.1f} in 2019 to {F(le_low,'LEx'):.1f} in {le_low}",
  'milestones': f"topped 8 billion in {first(8e9)}", 'm9': f"9 billion in {first(9e9)} and 10 billion in {first(10e9)}",
}
for k, v in exp.items(): chk(v in text, f'{k} = {v}')
for k in ['billions', 'per day', 'pop 2100']: chk(exp[k] in ld, f'JSON-LD has {k} = {exp[k]}')
for yr in yrs: chk(c(P('WORLD', yr)) in text, f'table {yr}')
csvt = [l.split(',') for l in open('dist/data/world-population.csv').read().splitlines() if re.match(r'^\d{4},', l)]
chk([int(r[0]) for r in csvt] == yrs, 'CSV years')
for r in csvt:
    yr = int(r[0]); urb = '' if yr > 2050 else str(round(U[yr], 1))
    chk(int(r[1]) == P('WORLD', yr) and r[2] == str(round(F(yr, 'PopDensity'))) and float(r[3]) == round(F(yr, 'TFR'), 2) and float(r[4]) == round(F(yr, 'MedianAgePop'), 1) and (r[5] == urb or (urb and float(r[5]) == float(urb))), f'CSV row {yr}')
chk(f'data-anchor="{P("WORLD", Y)}"' in page and f'data-rate="{K("WORLD", Y, "PopChange")}"' in page and 'data-date="2026-07-01"' in page, 'live counter anchor/rate/date')
print(f'\nRESULT world:', 'ALL MATCH' if not bad else f'{bad} mismatches', f'({n} checks)')
sys.exit(bad > 0)
