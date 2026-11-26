# Run after `npm run build`: python3 scripts/verify/croatia.py
# Independent check of every figure on /population/croatia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'HRV'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/croatia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert max(R, key=lambda yr: P(I, yr)) == 1990 and [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == list(range(1991, 2002)) + list(range(2008, y + 1))
assert P(I, y) < P(I, 1950) and next(yr for yr in R if K(I, yr, 'Births') < K(I, yr, 'Deaths')) == 1991 and all(K(I, yr, 'Births') < K(I, yr, 'Deaths') for yr in range(1991, 2101))
assert min(R, key=NM) == 1996 and all(NM(yr) < 0 for yr in range(1991, 2001)) and F(1991, 'LEx') < F(1990, 'LEx') - 1 and 0.55 < P(I, 2100) / P(I, y) < 0.57
assert sorted(countries(y, 1e6, EUROPE), key=lambda k: -K(k, y, 'Deaths') / K(k, y, 'Births')).index(I) == 7
exp = exp_base(I, y, U) | {
 'pk': f"1990, with {m(P(I, 1990))}", 'out': f"the heaviest {c(-NM(1996))} in 1996", 'le': f"from {F(1990, 'LEx'):.1f} years in 1990 to {F(1991, 'LEx'):.1f} in 1991", 'o17': f"reached {c(-NM(2017))} in 2017",
 'nat': f"a projected {c(K(I, y, 'Deaths'))} deaths and {c(K(I, y, 'Births'))} births", 'fut': f"leaves {m(P(I, 2100))} in the last projected year", 'f50': f"after {m(P(I, 2050))} at mid-century",
 'ld': f"1996, with {c(-NM(1996))}",
}
sys.exit(run('croatia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
