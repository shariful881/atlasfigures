# Run after `npm run build`: python3 scripts/verify/central-african-republic.py
# Independent check of every figure on /country/central-african-republic/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'CAF'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/central-african-republic.json'))['tableYears']
big1 = countries(y, 1e6)
assert min(big1, key=lambda k: f(k, y, 'MedianAgePop')) == I and min(big1, key=lambda k: min(f(k, yr, 'LEx') for yr in range(2000, y + 1))) == I
assert all(F(yr, 'LEx') < 35 and K(I, yr, 'Deaths') > 2 * K(I, yr - 1, 'Deaths') for yr in (2009, 2019, 2022)) and F(2023, 'LEx') > 55
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [2009, 2010, 2014, 2022] and min(R, key=lambda yr: K(I, yr, 'NetMigrations')) == 2014
assert sorted(countries(y, 1e6, AFRICA), key=lambda k: f(k, y, 'PopDensity')).index(I) == 4 and sorted(big1, key=lambda k: -f(k, y, 'TFR')).index(I) == 3
assert next(yr for yr in R if U.get(yr) and U[yr] > 50) == 2038 and max(R, key=lambda yr: P(I, yr)) == 2100 and 3.2 < P(I, 2100) / P(I, y) < 3.4
exp = exp_base(I, y, U) | {
 'bd': f"{c(K(I, y, 'Births'))} births are expected this year against {c(K(I, y, 'Deaths'))} deaths",
 'd': f"deaths jump to {c(K(I, 2009, 'Deaths'))} in 2009, {c(K(I, 2019, 'Deaths'))} in 2019 and {c(K(I, 2022, 'Deaths'))} in 2022",
 'le': f"falls to {F(2009, 'LEx'):.1f}, {F(2019, 'LEx'):.1f} and {F(2022, 'LEx'):.1f} years", 'le23': f"back at {F(2023, 'LEx'):.1f}",
 'out': f"heaviest in 2014, at {c(-K(I, 2014, 'NetMigrations'))}; in 2026 they are {c(-K(I, y, 'NetMigrations'))}",
 'fut': f"reach {m(P(I, 2050))} in 2050; by 2100, {m(P(I, 2100))}",
 'ld': f"The heaviest net departures, {c(-K(I, 2014, 'NetMigrations'))}, came in 2014",
}
sys.exit(run('central-african-republic', I, exp, ['population (millions)', 'ld'], yrs) > 0)
