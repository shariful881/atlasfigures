# Run after `npm run build`: python3 scripts/verify/greece.py
# Independent check of every figure on /population/greece/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'GRC'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/greece.json'))['tableYears']
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2010 and all(P(I, yr) < P(I, yr - 1) for yr in range(2011, 2101))
assert next(yr for yr in R if K(I, yr, 'NatChange') < 0) == 2011 and all(K(I, yr, 'NatChange') < 0 for yr in range(2011, 2101)) and 0.62 < P(I, 2100) / P(I, y) < 0.65
assert all(K(I, yr, 'NetMigrations') < 0 for yr in (2011, 2012, 2013, 2014, 2015, 2021, 2022, 2023, 2024)) and all(K(I, yr, 'NetMigrations') > 0 for yr in (2010, 2016, 2025))
out = min(range(1950, y + 1), key=lambda yr: K(I, yr, 'NetMigrations')); bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert (out, bt) == (2021, 1967)
assert sorted(countries(y, 1e6, EUROPE), key=lambda k: -f(k, y, 'MedianAgePop'))[:3] == ['ITA', 'PRT', I] and P(I, pk) - P(I, y) > 1e6
assert sorted(countries(y, 0, {'925'}), key=lambda k: -P(k, y))[:4] == ['ITA', 'ESP', 'PRT', I] and next(yr for yr in range(1951, 2101) if F(yr, 'TFR') < 2.1) == 1982
exp = exp_base(I, y, U) | {
 'pk': f"The high point, {m(P(I, pk))}, came in 2010", 'lost': f"Today's count is {m(P(I, pk) - P(I, y))} lower", 'gap': f"About {c(K(I, y, 'Deaths') - K(I, y, 'Births'))} in {y}",
 'bd': f"{c(K(I, y, 'Deaths'))} deaths and {c(K(I, y, 'Births'))} births, not much over a third of 1967's {c(K(I, bt, 'Births'))}", 'tfr': f"it is {F(y, 'TFR'):.2f} today",
 'mig': f"({c(-K(I, 2012, 'NetMigrations'))} in 2012)", 'out': f"the largest, {c(-K(I, out, 'NetMigrations'))}, in 2021", 'now': f"small net gain of {c(K(I, y, 'NetMigrations'))}",
 'fut': f"{m(P(I, 2100))}, with {m(P(I, 2050))} as the 2050 waypoint",
 'ld': f"the largest being {c(-K(I, out, 'NetMigrations'))} in 2021",
}
sys.exit(run('greece', I, exp, ['population (millions)', 'ld'], yrs) > 0)
