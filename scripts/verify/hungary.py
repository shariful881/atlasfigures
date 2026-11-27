# Run after `npm run build`: python3 scripts/verify/hungary.py
# Independent check of every figure on /country/hungary/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'HUN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/hungary.json'))['tableYears']
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 1980 and [yr for yr in range(1981, 2101) if P(I, yr) >= P(I, yr - 1)] == [2023]
assert next(yr for yr in R if K(I, yr, 'NatChange') < 0) == 1981 and all(K(I, yr, 'NatChange') < 0 for yr in range(1981, 2101)) and 1.02 < P(I, y) / P(I, 1950) < 1.04 and 1e6 < P(I, pk) - P(I, y) < 1.2e6
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 1956 and K(I, 1955, 'NetMigrations') > 0 and K(I, 1958, 'NetMigrations') > 0 and P(I, 1957) < P(I, 1956)
bl = min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')); bt = max(R, key=lambda yr: K(I, yr, 'Births')); tl = min(range(1950, y + 1), key=lambda yr: F(yr, 'TFR')); assert (bl, bt, tl) == (y, 1954, 2011)
assert [yr for yr in range(1959, y + 1) if F(yr, 'TFR') >= 2.1] == [1974, 1975, 1976, 1977] and sorted(countries(y, 0, {'923'}), key=lambda k: -P(k, y)).index(I) == 5
exp = exp_base(I, y, U) | {
 'pk': f"It reached {m(P(I, pk))} in 1980", 'lost': f"sits {m(P(I, pk) - P(I, y))} under the peak", 'bd': f"{c(K(I, y, 'Deaths'))} deaths and {c(K(I, y, 'Births'))} births", 'bt': f"the most were {c(K(I, bt, 'Births'))}, in {bt}",
 'tfr': f"it touched {F(tl, 'TFR'):.2f} in {tl} and is {F(y, 'TFR'):.2f} now", 'mig': f"departures exceed arrivals by {c(-K(I, 1956, 'NetMigrations'))} in 1956 and {c(-K(I, 1957, 'NetMigrations'))} in 1957",
 'fut': f"{m(P(I, 2050))} is the 2050 projection, {m(P(I, 2100))} the 2100 one", '1950': f"the {m(P(I, 1950))} of 1950",
 'ld': f"A net outflow of {c(-K(I, 1956, 'NetMigrations'))}",
}
sys.exit(run('hungary', I, exp, ['population (millions)', 'ld'], yrs) > 0)
