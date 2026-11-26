# Run after `npm run build`: python3 scripts/verify/papua-new-guinea.py
# Independent check of every figure on /population/papua-new-guinea/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'PNG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/papua-new-guinea.json'))['tableYears']
assert sorted(countries(y, 1e6), key=lambda k: urban(k)[y])[0] == I and U[1950] < 2 and abs(U[2000] - U[1980]) < 0.5 and U[2050] > 2 * U[y] - 1
assert F(1950, 'LEx') < 40 and 7 < P(I, y) / P(I, 1950) < 7.2
tm = max(R, key=lambda yr: F(yr, 'TFR')); r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert (tm, r21, bt) == (1969, 2070, 2046)
assert max(R, key=lambda yr: P(I, yr)) == 2100 and sorted(countries(y, 0, {'928'}), key=lambda k: -P(k, y))[0] == I and 10 * P('FJI', y) < P(I, y) and -5000 < K(I, y, 'NetMigrations') < 0 and SR(I, y) > 100
exp = exp_base(I, y, U) | {
 'urb': f"the urban share was {p1(U[1950])} in 1950, reached {p1(U[1980])} by 1980, was still {p1(U[2000])} in 2000", 'u50': f"to {p1(U[2050])}, by 2050",
 'le': f"expect to live {F(1950, 'LEx'):.1f} years; in 1970, {F(1970, 'LEx'):.1f}; in 2000, {F(2000, 'LEx'):.1f}", 'gain': f"risen by some {round(F(y, 'LEx') - F(1950, 'LEx'))} years", 'imr': f"Infant deaths run at {F(y, 'IMR'):.1f}",
 'tfr': f"Fertility peaked at {F(tm, 'TFR'):.2f} per woman in {tm} and has since fallen to {F(y, 'TFR'):.2f}; the projection keeps it above 2.1 until {r21}", 'mig': f"a net loss of {c(-K(I, y, 'NetMigrations'))} this year",
 'fut': f"reaching {m(P(I, 2100))} in 2100 and still rising, after {m(P(I, 2050))} in 2050",
 'ld': f"{c(K(I, y, 'Births'))} births outnumbering {c(K(I, y, 'Deaths'))} deaths",
}
sys.exit(run('papua-new-guinea', I, exp, ['population (millions)', 'ld'], yrs) > 0)
