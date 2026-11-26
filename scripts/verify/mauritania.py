# Run after `npm run build`: python3 scripts/verify/mauritania.py
# Independent check of every figure on /population/mauritania/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'MRT'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/mauritania.json'))['tableYears']
assert U[1950] < 3 and U[y] > 60 and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 2014
assert sorted(countries(y, 1e6, AFRICA), key=lambda k: f(k, y, 'PopDensity'))[:4] == ['NAM', 'LBY', 'BWA', I]
assert 8.2 < P(I, y) / P(I, 1950) < 8.4 and F(1950, 'IMR') > 180 and F(y, 'IMR') < 28 and all(F(yr, 'TFR') > 2.1 for yr in R) and max(R, key=lambda yr: F(yr, 'TFR')) == 1977
assert max(R, key=lambda yr: P(I, yr)) == 2100 and 3 < P(I, 2100) / P(I, y) < 3.2
exp = exp_base(I, y, U) | {
 'u': f"{p1(U[1950])} in 1950, {p1(U[1970])} in 1970 and {p1(U[1990])} in 1990", 'imr': f"Of every 1,000 births, {F(1950, 'IMR'):.1f} ended in an infant death in 1950; today {F(y, 'IMR'):.1f} do",
 'le': f"from {F(1950, 'LEx'):.1f} years to {F(y, 'LEx'):.1f}", 'tfr': f"(it peaked in 1977, at {F(1977, 'TFR'):.2f}) is {F(y, 'TFR'):.2f} today", 'fut': f"{m(P(I, 2050))} around mid-century, {m(P(I, 2100))} by 2100",
 'ld': f"4.48 now and {F(2100, 'TFR'):.2f} in the last projected year",
}
sys.exit(run('mauritania', I, exp, ['population (millions)', 'ld'], yrs) > 0)
