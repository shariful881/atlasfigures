# Run after `npm run build`: python3 scripts/verify/zambia.py
# Independent check of every figure on /country/zambia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'ZMB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/zambia.json'))['tableYears']
ALL = countries(y); EAF = {'910'}
uh = max(range(1950, 2001), key=lambda yr: U[yr]); assert uh == 1980 and min(range(1980, 2001), key=lambda yr: U[yr]) == 2000
back = next(yr for yr in range(1981, 2051) if U[yr] > U[uh]); half = next(yr for yr in range(y, 2051) if U[yr] > 50); assert (back, half) == (2010, 2034)
lo = min(range(1980, y + 1), key=lambda yr: F(yr, 'LEx')); lb = next(yr for yr in range(lo, y + 1) if F(yr, 'LEx') > F(1980, 'LEx')); assert (lo, lb) == (1998, 2009)
gain = lambda k: f(k, y, 'LEx') - f(k, 2000, 'LEx'); assert sorted(ALL, key=lambda k: -gain(k)).index(I) == 2
ml = min(range(1950, y + 1), key=lambda yr: F(yr, 'MedianAgePop')); assert ml == 1980
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert (tmax, under) == (1975, 2098)
ov = next(yr for yr in range(y, 2101) if P(I, yr) > P('MWI', yr)); assert ov == 2034 and P(I, y) < P('MWI', y)
assert sorted(countries(y, 0, EAF), key=lambda k: -P(k, y)).index(I) == 7 and all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101))
exp = exp_base(I, y, U) | {
 'urban': f"rising to {p1(U[uh])} by {uh} (it was {p1(U[1950])} in 1950) and sliding to {p1(U[2000])} by 2000", 'back': f"again until {back}", 'half': f"projected for {half}",
 'le': f"By {F(1980, 'LEx') - F(lo, 'LEx'):.1f} years: from {F(1980, 'LEx'):.1f} at birth in 1980 to {F(lo, 'LEx'):.1f} in {lo}", 'lb': f"the 1980 figure until {lb}",
 'gain': f"risen {gain(I):.1f} years, to {F(y, 'LEx'):.1f}", 'times': f"About {P(I, y) / P(I, 1950):.1f}-fold over {y - 1950} years", 'p1950': f"the 1950 figure ({m(P(I, 1950))})",
 'median low': f"from a low of {F(ml, 'MedianAgePop'):.1f} in {ml}", 'tfr': f"reached {F(tmax, 'TFR'):.2f} in {tmax}, its high, is {F(y, 'TFR'):.2f} now", 'under': f"under 2.1 only in {under}",
 'ov': f"In {ov}, on the UN medium variant", 'pops': f"2050 total of {m(P(I, 2050))} grows to {m(P(I, 2100))} by 2100", 'ranks': f"from {ordn(rank(I, y))} to {ordn(rank(I, 2100))}",
 'ld': f"It fell from {F(1980, 'LEx'):.1f} years in 1980 to {F(lo, 'LEx'):.1f} in {lo}, regained the 1980 level in {lb}",
}
sys.exit(run('zambia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
