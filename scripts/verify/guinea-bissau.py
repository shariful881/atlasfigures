# Run after `npm run build`: python3 scripts/verify/guinea-bissau.py
# Independent check of every figure on /population/guinea-bissau/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'GNB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/guinea-bissau.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert min(R, key=lambda yr: F(yr, 'LEx')) == 1963 and all(P(I, yr) < P(I, yr - 1) for yr in range(1964, 1967)) and all(P(I, yr) > P(I, yr - 1) for yr in range(1967, 2101))
assert all(NM(yr) < 0 for yr in range(1963, 1967)) and min(R, key=NM) == 1964 and max(R, key=NM) == 1977
assert all(K(I, yr, 'Births') > K(I, yr, 'Deaths') for yr in R) and all(U[yr] < 50 for yr in range(1950, 2051))
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1985 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2079 and 2 < P(I, 2100) / P(I, y) < 2.1
exp = exp_base(I, y, U) | {
 'dip': f"Lifespans bottomed at {F(1963, 'LEx'):.1f} years in 1963", 'out': f"(the most, {c(-NM(1964))}, in 1964), and the count slid from {c(P(I, 1963))} to {c(P(I, 1966))}",
 'u': f"{p1(U[y])} urban now, up from {p1(U[1950])} in 1950, and still short of half at {p1(U[2050])}", 'fut': f"About twice its current size, {m(P(I, 2100))}, by 2100",
 'tfr': f"The 1985 fertility peak, {F(1985, 'TFR'):.2f}, has given way to {F(y, 'TFR'):.2f} today", 'in': f"The biggest migration gain came in 1977, {c(NM(1977))}",
 'ld': f"1977: {c(NM(1977))} more arrived than left",
}
sys.exit(run('guinea-bissau', I, exp, ['population (millions)', 'ld'], yrs) > 0)
