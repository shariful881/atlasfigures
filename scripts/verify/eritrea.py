# Run after `npm run build`: python3 scripts/verify/eritrea.py
# Independent check of every figure on /population/eritrea/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'ERI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/eritrea.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert min(R, key=NM) == 1991 and 0.155 < -NM(1991) / P(I, 1990) < 0.165 and max(R, key=NM) == 1995 and NM(1993) > 0
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1991, 1992] and max(R, key=lambda yr: P(I, yr)) == 2100
assert min(R, key=lambda yr: F(yr, 'LEx')) == 1957 and F(1999, 'LEx') < F(1997, 'LEx') and all(U[yr] < 50 for yr in range(1950, 2051))
assert next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2080 and 4.4 < P(I, y) / P(I, 1950) < 4.6
exp = exp_base(I, y, U) | {
 'out': f"{c(-NM(1991))} net, around 16% of the {m(P(I, 1990))} estimated for 1990", 'in': f"1995 logged {c(NM(1995))} net arrivals", 'n93': c(NM(1993)),
 'le': f"Two troughs: {F(1957, 'LEx'):.1f} years in 1957, the series minimum, and {F(1999, 'LEx'):.1f} in 1999, having been {F(1997, 'LEx'):.1f} in 1997",
 'urb': f"Urban residents made up {p1(U[1950])} in 1950, {p1(U[y])} now and are expected at {p1(U[2050])} for 2050",
 'fut': f"{m(P(I, 2050))} around 2050, {m(P(I, 2100))} at the close", 'tfr2080': "drops under 2.1 in 2080",
 'ld': f"Chiefly 1995, whose {c(NM(1995))} net arrivals top the series",
}
sys.exit(run('eritrea', I, exp, ['population (millions)', 'ld'], yrs) > 0)
