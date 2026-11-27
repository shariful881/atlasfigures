# Run after `npm run build`: python3 scripts/verify/israel.py
# Independent check of every figure on /country/israel/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'ISR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/israel.json'))['tableYears']
M80 = [k for k in countries(y, 1e6) if f(k, y, 'LEx') >= 80]
assert sorted(M80, key=lambda k: -f(k, y, 'TFR'))[0] == I and sorted(M80, key=lambda k: f(k, y, 'MedianAgePop'))[0] == I and 7.3 < P(I, y) / P(I, 1950) < 7.6
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert inn == 1990 and K(I, 1991, 'NetMigrations') > 1.5e5 and [yr for yr in R if K(I, yr, 'NetMigrations') < 0] == [1985, 1986]
r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); db = next(yr for yr in R if P(I, yr) >= 2 * P(I, y)); assert (r21, bt, db) == (2069, 2081, 2096) and all(F(yr, 'TFR') > 2.1 for yr in range(1950, 2051))
assert max(R, key=lambda yr: P(I, yr)) == 2100 and sorted(countries(y, 1e6), key=lambda k: -f(k, y, 'PopDensity')).index(I) == 13 and 3 * K(I, y, 'Deaths') < K(I, y, 'Births')
exp = exp_base(I, y, U) | {
 'bd': f"Births, {c(K(I, y, 'Births'))} this year, are more than three times deaths, {c(K(I, y, 'Deaths'))}", 'med': f"the youngest median age, {F(y, 'MedianAgePop'):.1f}",
 'in': f"1990, {c(K(I, 1990, 'NetMigrations'))}, and 1991, {c(K(I, 1991, 'NetMigrations'))}", 'now': f"this year it is {c(K(I, y, 'NetMigrations'))}",
 'fut': f"crosses that mark in {db} and shows {m(P(I, 2100))} for 2100", 'tfr': f"until {r21} in the projection, and yearly births go on rising until {bt}",
 'ld': f"net gains of {c(K(I, 1990, 'NetMigrations'))} and {c(K(I, 1991, 'NetMigrations'))}",
}
sys.exit(run('israel', I, exp, ['population (millions)', 'ld'], yrs) > 0)
