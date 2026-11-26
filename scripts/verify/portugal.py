# Run after `npm run build`: python3 scripts/verify/portugal.py
# Independent check of every figure on /population/portugal/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'PRT'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/portugal.json'))['tableYears']
E1 = countries(y, 1e6, EUROPE)
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1970, 2021)
assert all(K(I, yr, 'NetMigrations') < 0 for yr in range(1950, 1971)) and K(I, 1971, 'NetMigrations') > 0
assert all(P(I, yr) < P(I, yr - 1) and K(I, yr, 'NatChange') > 0 and K(I, yr, 'NetMigrations') < -K(I, yr, 'NatChange') for yr in range(1964, 1971)) and P(I, 1963) > P(I, 1962)
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2010 and next(yr for yr in R if K(I, yr, 'NatChange') < 0) == 2009 and all(K(I, yr, 'NatChange') < 0 for yr in range(2009, 2101))
assert sorted(E1, key=lambda k: -f(k, y, 'MedianAgePop'))[:2] == ['ITA', I] and SR(I, y) < 92
bt = max(R, key=lambda yr: K(I, yr, 'Births')); r21 = next(yr for yr in range(1963, 2101) if F(yr, 'TFR') < 2.1); assert (bt, r21) == (1962, 1982) and all(F(yr, 'TFR') < 2.1 for yr in range(1982, y + 1))
assert sorted(countries(y, 0, {'925'}), key=lambda k: -P(k, y))[:3] == ['ITA', 'ESP', I] and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1994
exp = exp_base(I, y, U) | {
 'out': f"the 1970 outflow, {c(-K(I, out, 'NetMigrations'))}, was the largest", 'in71': f"net arrivals ({c(K(I, 1971, 'NetMigrations'))} that year)", 'pk': f"The 2010 count of {m(P(I, pk))} is the series high",
 'gap': f"the {y} gap is {c(K(I, y, 'Deaths') - K(I, y, 'Births'))}", 'in': f"largest in 2021 at {c(K(I, inn, 'NetMigrations'))}", 'fut': f"{m(P(I, 2050))} (2050) and {m(P(I, 2100))} (2100)",
 'b': f"The most births in any year, {c(K(I, bt, 'Births'))}, was recorded in {bt}, against a projected {c(K(I, y, 'Births'))} now", 'tfr': f"from 1982, is {F(y, 'TFR'):.2f}", 'sr': f"the sex ratio is {SR(I, y):.1f}", 'urb': f"majority-urban in 1994 (national definition); the share is {p1(U[y])}",
 'ld': f"{c(K(I, y, 'Deaths'))} deaths and {c(K(I, y, 'Births'))} births, with net arrivals of {c(K(I, y, 'NetMigrations'))}",
}
sys.exit(run('portugal', I, exp, ['population (millions)', 'ld'], yrs) > 0)
