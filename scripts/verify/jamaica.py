# Run after `npm run build`: python3 scripts/verify/jamaica.py
# Independent check of every figure on /population/jamaica/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'JAM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/jamaica.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); b1 = countries(y, 1e6)
assert [yr for yr in range(1952, y + 1) if NM(yr) >= 0] == [2020] and NM(2020) == 0 and NM(1950) > 0 and NM(1951) > 0 and min(R, key=NM) == 1967
assert max(R, key=lambda yr: P(I, yr)) == 2023 and all(P(I, yr) < P(I, yr - 1) for yr in range(2024, 2101))
assert sorted(b1, key=lambda k: P(k, 2100) / P(k, y))[:3] == ['HKG', 'PRI', I] and 0.37 < P(I, 2100) / P(I, y) < 0.38
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1964 and max(R, key=lambda yr: K(I, yr, 'Births')) == 1964 and min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y
assert next(yr for yr in R if K(I, yr, 'Deaths') > K(I, yr, 'Births')) == 2034 and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2034, 2101))
assert next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2006 and all(F(yr, 'TFR') < 2.1 for yr in range(2006, 2101))
exp = exp_base(I, y, U) | {
 'out': f"The heaviest year was 1967, at {c(-NM(1967))} net; 2026 expects {c(-NM(y))}", 'pk': f"The maximum, {m(P(I, 2023))}, was reached in 2023",
 'fut': f"Mid-century should bring {m(P(I, 2050))}, and the year 2100 just {m(P(I, 2100))}", 'b': f"1964 marks the top for both fertility ({F(1964, 'TFR'):.2f}) and births ({c(K(I, 1964, 'Births'))}); the 2026 figures are {F(y, 'TFR'):.2f} and {c(K(I, y, 'Births'))}",
 'ld': f"The largest outflow was {c(-NM(1967))} in 1967",
}
sys.exit(run('jamaica', I, exp, ['population (millions)', 'ld'], yrs) > 0)
