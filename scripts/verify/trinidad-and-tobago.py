# Run after `npm run build`: python3 scripts/verify/trinidad-and-tobago.py
# Independent check of every figure on /population/trinidad-and-tobago/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovenia.json'))['tableYears']
I = 'TTO'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/trinidad-and-tobago.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert all(NM(yr) < 0 for yr in range(1950, 2017)) and len(range(1950, 2017)) == 67 and NM(2017) > 0 and NM(2018) > 0 and NM(2019) < 0
assert all(NM(yr) > 0 for yr in range(2020, y + 1)) and NM(2027) < 0 and min(R, key=NM) == 2019 and max(R, key=NM) == 2018
assert max(R, key=lambda yr: P(I, yr)) == 2028 and all(P(I, yr) < P(I, yr - 1) for yr in range(2029, 2101)) and P(I, y) > P(I, y - 1)
assert all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2029, 2101)) and K(I, 2028, 'Deaths') <= K(I, 2028, 'Births')
assert min(yr for yr in R if U.get(yr, 0) > 50) == 1978 and max(R, key=lambda yr: K(I, yr, 'Births')) == 1983 and min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y
exp = exp_base(I, y, U) | {
 'in': f"the larger in 2018 at {c(NM(2018))}; 2019 then saw the biggest outflow, {c(-NM(2019))}", 'end': f"down to {c(round(P(I, 2100) / 1e3))} thousand at 2100",
 'b': f"Births, {c(K(I, 1983, 'Births'))} at their 1983 high, number {c(K(I, y, 'Births'))} in 2026", 'u50': f"expected at just {p1(U[2050])} in 2050",
 'le': f"recovered from {F(2021, 'LEx'):.1f} in 2021", 'pk': f"2028, with {m(P(I, 2028))}",
 'ld': f"largest net inflow ({c(NM(2018))})",
}
sys.exit(run('trinidad-and-tobago', I, exp, ['population (millions)', 'ld'], yrs) > 0)
