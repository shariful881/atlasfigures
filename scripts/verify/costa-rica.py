# Run after `npm run build`: python3 scripts/verify/costa-rica.py
# Independent check of every figure on /country/costa-rica/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'CRI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/costa-rica.json'))['tableYears']
cam = countries(y, 1e6, {'916'})
assert max(cam, key=lambda k: f(k, y, 'LEx')) == I and min(cam, key=lambda k: f(k, y, 'TFR')) == I and max(cam, key=lambda k: f(k, y, 'MedianAgePop')) == I
assert sorted(countries(y, 1e6, {'915', '916', '931'}), key=lambda k: f(k, y, 'TFR'))[:3] == ['PRI', 'CHL', I]
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1959 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2003 and all(F(yr, 'TFR') < 2.1 for yr in range(2003, 2101))
assert all(K(I, yr, 'NetMigrations') >= 0 for yr in R) and max(R, key=lambda yr: K(I, yr, 'Births')) == 1987 and max(R, key=lambda yr: P(I, yr)) == 2044
assert 0.72 < P(I, 2100) / P(I, y) < 0.74 and 5.5 < P(I, y) / P(I, 1950) < 5.7
exp = exp_base(I, y, U) | {
 'tfr': f"{F(1959, 'TFR'):.2f} as the 1959 average, {F(1980, 'TFR'):.2f} by 1980", 'b': f"Annual births reached their maximum, {c(K(I, 1987, 'Births'))}, in 1987",
 'le50': f"against {F(1950, 'LEx'):.1f} in 1950", 'nm': f"topping out at {c(K(I, 1996, 'NetMigrations'))} in 1996; for 2026 it is {c(K(I, y, 'NetMigrations'))}",
 'pk': f"highest in 2044 ({m(P(I, 2044))}), then shrinks to {m(P(I, 2100))}",
 'ld': f"Costa Rica, at {F(y, 'LEx'):.1f} years by UN estimate",
}
sys.exit(run('costa-rica', I, exp, ['population (millions)', 'ld'], yrs) > 0)
