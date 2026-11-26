# Run after `npm run build`: python3 scripts/verify/equatorial-guinea.py
# Independent check of every figure on /population/equatorial-guinea/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
AF = {'910', '911', '912', '913', '914'}
I = 'GNQ'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/equatorial-guinea.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); af = countries(y, 1e6, AF)
assert max(af, key=lambda k: SR(k, y)) == I and min(R, key=lambda yr: F(yr, 'LEx')) == 1976 and F(1969, 'LEx') < 32 and F(1968, 'LEx') > 44
assert all(P(I, yr) < P(I, yr - 1) for yr in range(1970, 1979)) and all(P(I, yr) > P(I, yr - 1) for yr in range(1979, 2101))
assert all(NM(yr) < 0 for yr in range(1969, 1980)) and all(NM(yr) > 0 for yr in range(1980, 2020)) and len(range(1980, 2020)) == 40 and min(R, key=NM) == 1973 and max(R, key=NM) == 2004
assert 8.7 < P(I, y) / P(I, 1950) < 8.9 and next(yr for yr in range(1950, 2051) if U[yr] > 50) == 2009
exp = exp_base(I, y, U) | {
 'p': f"the headcount dropped, from {c(P(I, 1969))} to {c(P(I, 1978))}", 'out': f"heaviest in 1973 ({c(-NM(1973))})", 'le': f"plunged to {F(1969, 'LEx'):.1f} in 1969 and to {F(1976, 'LEx'):.1f} in 1976",
 'sr': f"{SR(I, y):.1f} males for each hundred females", 'in': f"with 2004 the busiest ({c(NM(2004))})", 'g': f"close to 8.8 times 1950's {c(P(I, 1950))}",
 'fut': f"Ahead: {m(P(I, 2050))} as of 2050; {m(P(I, 2100))} as of 2100",
 'ld': f"2004, at {c(NM(2004))} net",
}
sys.exit(run('equatorial-guinea', I, exp, ['population (millions)', 'ld'], yrs) > 0)
