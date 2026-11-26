# Run after `npm run build`: python3 scripts/verify/tunisia.py
# Independent check of every figure on /population/tunisia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'TUN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/tunisia.json'))['tableYears']
ALL = countries(y); A1 = countries(y, 1e6, AFRICA)
assert [yr for yr in range(1950, y + 1) if F(yr, 'TFR') < 2.1] == list(range(1999, 2011)) + list(range(2020, y + 1))
reb = max(range(2011, 2020), key=lambda yr: F(yr, 'TFR')); assert reb == 2014; tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1963
assert sorted(countries(2000), key=lambda k: -(f(k, 1963, 'TFR') - f(k, 2000, 'TFR'))).index(I) == 3
assert sorted(A1, key=lambda k: -f(k, y, 'LEx'))[0] == I and sorted(A1, key=lambda k: -f(k, y, 'MedianAgePop'))[:2] == ['MUS', I] and sorted(A1, key=lambda k: f(k, y, 'TFR'))[:2] == ['MUS', I]
men = [yr for yr in R if SR(I, yr) > 100]; assert men == list(range(1970, 2010)) + list(range(2087, 2101))
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2051; nn = next(yr for yr in R if K(I, yr, 'NatChange') < 0); assert nn == 2055
bt = max(R, key=lambda yr: K(I, yr, 'Births')); b2 = max(range(2000, 2101), key=lambda yr: K(I, yr, 'Births')); assert (bt, b2) == (1986, 2014)
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 1976
exp = exp_base(I, y, U) | {
 'tfr99': f"slipped to {F(1999, 'TFR'):.2f} in 1999", 'reb': f"peaking at {F(reb, 'TFR'):.2f} in {reb}", 'births': f"{c(K(I, 2014, 'Births'))} in 2014, a 21st-century high, though short of the {c(K(I, 1986, 'Births'))} recorded in 1986",
 'fall': f"from {F(1963, 'TFR'):.2f} per woman (1963) to {F(2000, 'TFR'):.2f} in 2000", 'le': f"from {F(2019, 'LEx'):.1f} in 2019 to {F(2021, 'LEx'):.1f} in 2021, and a return to {F(2022, 'LEx'):.1f}", 'sr': f"now there are {SR(I, y):.1f} of them",
 'pk': f"its high, {m(P(I, pk))}, in {pk}. Deaths then outpace births starting in {nn}, and 2100 ends at {m(P(I, 2100))}", 'urb': f"majority-urban in {half}",
 'ld': f"reaching {F(reb, 'TFR'):.2f} in 2014, before falling again",
}
sys.exit(run('tunisia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
