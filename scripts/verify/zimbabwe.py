# Run after `npm run build`: python3 scripts/verify/zimbabwe.py
# Independent check of every figure on /country/zimbabwe/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'ZWE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/zimbabwe.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); EAF = {'910'}
lt = max(range(1950, 2000), key=lambda yr: F(yr, 'LEx')); ll = min(range(1990, y + 1), key=lambda yr: F(yr, 'LEx')); lb = next(yr for yr in range(ll + 1, 2101) if F(yr, 'LEx') > F(lt, 'LEx'))
assert (lt, ll, lb) == (1986, 2001, 2019) and sorted(ALL, key=lambda k: -(f(k, y, 'LEx') - f(k, 2000, 'LEx'))).index(I) == 5
it = max(range(1985, 2006), key=lambda yr: F(yr, 'IMR')); assert it == 1996 and F(it, 'IMR') > F(1990, 'IMR') + 5
assert all(SR(I, yr) < 100 for yr in R); sl = min(R, key=lambda yr: SR(I, yr)); assert sl == 2013 and sorted(B, key=lambda k: SR(k, y)).index(I) == 4
assert max(yr for yr in R if K(I, yr, 'NetMigrations') > 0) == 1998; out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1993, 1980)
assert [yr for yr in range(1950, 2100) if K(I, yr, 'PopChange') < 0] == [1993] and all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101))
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 2041 and abs(U[2010] - U[2000]) < 0.5 and sorted(countries(y, 0, EAF), key=lambda k: -P(k, y)).index(I) == 9
exp = exp_base(I, y, U) | {
 'le': f"From {F(lt, 'LEx'):.1f} years in {lt} to {F(ll, 'LEx'):.1f} in {ll} in the UN estimates, a loss of {F(lt, 'LEx') - F(ll, 'LEx'):.1f} years", 'imr': f"{F(1990, 'IMR'):.1f} deaths per thousand births in 1990, {F(it, 'IMR'):.1f} by {it}",
 'lb': f"passed again in {lb}", 'sr': f"bottomed out in {sl} at {SR(I, sl):.1f} men to every 100 women and is {SR(I, y):.1f} now", 'mig': f"by some {k1(-K(I, y, 'NetMigrations'))} in {y}",
 'out': f"{out} holds the record net outflow (near {k1(-K(I, out, 'NetMigrations'))}) and {inn} the record inflow (around {k1(K(I, inn, 'NetMigrations'))})",
 'p2100': f"ending at {m(P(I, 2100))}", 'tfr': f"Fertility is {F(y, 'TFR'):.2f}, down from {F(1960, 'TFR'):.2f} in 1960", 'urb': f"the share is {p1(U[y])} today; a majority is projected for {half}",
 'ld': f"still climbing in 2100, at {m(P(I, 2100))}; mid-century brings {m(P(I, 2050))}",
}
sys.exit(run('zimbabwe', I, exp, ['population (millions)', 'ld'], yrs) > 0)
