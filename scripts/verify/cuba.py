# Run after `npm run build`: python3 scripts/verify/cuba.py
# Independent check of every figure on /country/cuba/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'CUB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/cuba.json'))['tableYears']
L1 = countries(y, 1e6, {'915', '916', '931'})
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2012 and all(P(I, yr) < P(I, yr - 1) for yr in range(2013, 2101))
lost = P(I, pk) - P(I, y); assert 3.5 < lost / P(I, pk) * 100 < 3.7
assert [yr for yr in R if K(I, yr, 'NatChange') < 0][0] == 2019 and all(K(I, yr, 'NatChange') < 0 for yr in range(2019, 2101)) and all(K(I, yr, 'NetMigrations') < 0 for yr in R)
assert 0.5 < P(I, 2100) / P(I, y) < 0.52
f21 = lambda k: next((yr for yr in R if f(k, yr, 'TFR') < 2.1), 9999); assert sorted(L1, key=f21)[0] == I and f21(I) == 1978 and all(F(yr, 'TFR') < 2.1 for yr in range(1978, y + 1))
tm = max(R, key=lambda yr: F(yr, 'TFR')); bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert (tm, bt) == (1963, 1965)
assert sorted(L1, key=lambda k: f(k, y, 'IMR'))[0] == I and sorted(L1, key=lambda k: -f(k, y, 'MedianAgePop'))[:2] == ['PRI', I] and sorted(countries(y, 0, {'915'}), key=lambda k: -P(k, y))[:3] == ['HTI', 'DOM', I]
exp = exp_base(I, y, U) | {
 'pk': f"peaks at {m(P(I, pk))} in 2012", 'lost': f"the {y} figure is {c(lost)} below the peak", 'fut': f"leaving {m(P(I, 2050))} by 2050 and only {m(P(I, 2100))} by 2100",
 'gap': f"Some {c(K(I, y, 'Deaths') - K(I, y, 'Births'))} this year", 'bd': f"{c(K(I, y, 'Deaths'))} deaths and only {c(K(I, y, 'Births'))} births, roughly a third of the {c(K(I, bt, 'Births'))} born in {bt}", 'mig': f"{c(-K(I, y, 'NetMigrations'))} in {y}",
 'tfr': f"In 1978, at {F(1978, 'TFR'):.2f}", 'tfr2': f"The rate had been {F(tm, 'TFR'):.2f} in {tm}; it is {F(y, 'TFR'):.2f} now", 'med': f"Cuba's median age is {F(y, 'MedianAgePop'):.1f}", 'imr': f"infant mortality rate, just {F(y, 'IMR'):.1f}", 'le21': f"fell to {F(2021, 'LEx'):.1f} in 2021",
 'ld': f"adding up to about {p1(lost / P(I, pk) * 100)} so far",
}
sys.exit(run('cuba', I, exp, ['population (millions)', 'ld'], yrs) > 0)
