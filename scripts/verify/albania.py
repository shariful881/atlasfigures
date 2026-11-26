# Run after `npm run build`: python3 scripts/verify/albania.py
# Independent check of every figure on /population/albania/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
EU = {'923', '924', '925', '926'}
I = 'ALB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/albania.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); eu = countries(y, 1e6, EU)
assert max(R, key=lambda yr: P(I, yr)) == 1991 and all(NM(yr) < 0 for yr in range(1989, 2101)) and NM(1988) >= 0 and min(R, key=NM) == 1994
assert [yr for yr in range(1992, y + 1) if P(I, yr) > P(I, yr - 1)] == [2017] and max(eu, key=lambda k: f(k, y, 'LEx') - f(k, 1950, 'LEx')) == I and 35 < F(y, 'LEx') - F(1950, 'LEx') < 36
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1955 and max(R, key=lambda yr: K(I, yr, 'Births')) == 1990 and min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y and K(I, y, 'Births') < K(I, 1990, 'Births') / 3
assert next(yr for yr in range(1950, 2051) if U[yr] > 50) == 2009 and 0.42 < P(I, 2100) / P(I, y) < 0.44 and all(F(yr, 'TFR') < 2.1 for yr in range(2002, 2101)) and F(2001, 'TFR') >= 2.1
exp = exp_base(I, y, U) | {
 'out': f"The peak year was 1994, {c(-NM(1994))} net; 2026 expects {c(-NM(y))}", 'le': f"life expectancy went from {F(1950, 'LEx'):.1f} to {F(y, 'LEx'):.1f}",
 'b': f"They collapsed after a 1990 peak of {c(K(I, 1990, 'Births'))}; 2026 expects {c(K(I, y, 'Births'))}", 'tfr': f"Fertility, {F(1955, 'TFR'):.2f} in 1955",
 'fut': f"Projections: {m(P(I, 2050))} as of 2050, then {m(P(I, 2100))}", 'pk': f"below its 1991 maximum, {m(P(I, 1991))}",
 'ld': f"The largest year was 1994, {c(-NM(1994))} net",
}
sys.exit(run('albania', I, exp, ['population (millions)', 'ld'], yrs) > 0)
