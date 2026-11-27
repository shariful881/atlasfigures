# Run after `npm run build`: python3 scripts/verify/togo.py
# Independent check of every figure on /country/togo/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'TGO'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/togo.json'))['tableYears']
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 1993 and -K(I, out, 'NetMigrations') > 3e5 and all(K(I, yr, 'NetMigrations') > 0 for yr in (1994, 1995, 1996))
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1993] and all(F(yr, 'TFR') > 2.1 for yr in R)
tm = max(R, key=lambda yr: F(yr, 'TFR')); bt = max(R, key=lambda yr: K(I, yr, 'Births')); pk = max(R, key=lambda yr: P(I, yr)); assert (tm, bt, pk) == (1974, 2083, 2100) and 2.6 < P(I, 2100) / P(I, y) < 2.8
assert sorted(countries(y, 1e6, {'914'}), key=lambda k: -f(k, y, 'PopDensity'))[:3] == ['GMB', 'NGA', I] and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 2034 and 6.2 < P(I, y) / P(I, 1950) < 6.4
exp = exp_base(I, y, U) | {
 'out': f"{c(-K(I, 1993, 'NetMigrations'))} people in the UN data", 'dip': f"by {c(P(I, 1992) - P(I, 1993))} against 1992", 'in': f"{c(K(I, 1994, 'NetMigrations'))} in 1994 and {c(K(I, 1995, 'NetMigrations'))} in 1995",
 'tfr': f"hit its high, {F(tm, 'TFR'):.2f}, in {tm}, is {F(y, 'TFR'):.2f} now", 'b': f"Births, {c(K(I, y, 'Births'))} this year, keep rising until {bt}", 'fut': f"To {m(P(I, 2100))}, nearly 2.7 times",
 'ld': f"Net departures of {c(-K(I, 1993, 'NetMigrations'))}",
}
sys.exit(run('togo', I, exp, ['population (millions)', 'ld'], yrs) > 0)
