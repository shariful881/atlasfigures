# Run after `npm run build`: python3 scripts/verify/armenia.py
# Independent check of every figure on /population/armenia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'ARM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/armenia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); b1 = countries(y, 1e6)
assert F(1988, 'LEx') < 53 and F(1987, 'LEx') > 67 and F(1989, 'LEx') > 67 and K(I, 1988, 'Deaths') > 1.9 * K(I, 1987, 'Deaths')
assert max(R, key=NM) == 1989 and min(R, key=NM) == 1992 and max(R, key=lambda yr: P(I, yr)) == 1991
assert [yr for yr in range(1992, 2101) if P(I, yr) > P(I, yr - 1)] == [2022, 2023, 2024] and NM(2022) > 0 and NM(2023) > 0 and NM(2024) < 0
assert next(yr for yr in range(1950, 2051) if U[yr] > 50) == 1959 and all(U[yr] > 50 for yr in range(1959, 2051)) and sorted(b1, key=lambda k: SR(k, y)).index(I) == 3
assert 2.05 < P(I, y) / P(I, 1950) < 2.2 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 1994 and all(F(yr, 'TFR') < 2.1 for yr in range(1994, 2101))
exp = exp_base(I, y, U) | {
 'eq': f"The UN series for that year carries {c(K(I, 1988, 'Deaths'))} deaths, against {c(K(I, 1987, 'Deaths'))} a year earlier, and a lifespan figure of {F(1988, 'LEx'):.1f}, flanked by {F(1987, 'LEx'):.1f} in 1987 and {F(1989, 'LEx'):.1f} in 1989",
 'mig': f"1989 holds the largest net inflow in the series, {c(NM(1989))}", 'out': f"the largest net outflow, {c(-NM(1992))}, and 1993 another {c(-NM(1993))}",
 'rec': f"showing {c(NM(2022))} and {c(NM(2023))} net newcomers", 'fut': f"{m(P(I, 2050))} at 2050 and then {m(P(I, 2100))} at 2100", 'p50': f"its 1950 size ({m(P(I, 1950))})",
 'sr': f"men number {SR(I, y):.1f} per 100 women", 'pk': f"After a 1991 summit of {m(P(I, 1991))}",
 'ld': f"1992: {c(-NM(1992))} net",
}
sys.exit(run('armenia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
