# Run after `npm run build`: python3 scripts/verify/haiti.py
# Independent check of every figure on /population/haiti/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'HTI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/haiti.json'))['tableYears']
LAT = {'915', '916', '931'}; L1 = countries(y, 1e6, LAT)
assert sorted(L1, key=lambda k: -f(k, y, 'PopDensity'))[0] == I and sorted(L1, key=lambda k: -f(k, y, 'TFR'))[0] == I and sorted(L1, key=lambda k: -f(k, y, 'IMR'))[0] == I and sorted(L1, key=lambda k: f(k, y, 'LEx'))[0] == I
assert sorted(countries(2010), key=lambda k: f(k, 2010, 'LEx') - f(k, 2009, 'LEx'))[0] == I and K(I, 2010, 'Deaths') > 2 * K(I, 2009, 'Deaths') and P(I, 2010) > P(I, 2009)
assert all(K(I, yr, 'NetMigrations') < 0 for yr in R); left = -sum(K(I, yr, 'NetMigrations') for yr in range(1950, y + 1)); assert 1.8e6 < left < 1.9e6
behind = [yr for yr in R if P(I, yr) < P('DOM', yr)]; assert behind == list(range(1977, 2013))
assert sorted(countries(y, 0, {'915'}), key=lambda k: -P(k, y))[0] == I
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2076; r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert r21 == 2047; half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 2016
exp = exp_base(I, y, U) | {
 'd10': f"puts them at {c(K(I, 2010, 'Deaths'))} for 2010, against {c(K(I, 2009, 'Deaths'))} in 2009", 'le': f"drops from {F(2009, 'LEx'):.1f} to {F(2010, 'LEx'):.1f} years", 'le11': f"recovers to {F(2011, 'LEx'):.1f} in 2011",
 'imr': f"infant deaths ({F(y, 'IMR'):.1f} for each 1,000 born)", 'left': f"close to {left / 1e6:.1f} million people", 'nat': f"{c(K(I, y, 'Births'))} births and {c(K(I, y, 'Deaths'))} deaths are expected this year, against net departures of {c(-K(I, y, 'NetMigrations'))}",
 '1950': f"in 1950 ({m(P(I, 1950))} against {m(P('DOM', 1950))})", 'pk': f"tops out in {pk} with {m(P(I, pk))}", 'urb': f"passed one half in {half}",
 'ld': f"versus {m(P('DOM', y))} in {y}",
}
sys.exit(run('haiti', I, exp, ['population (millions)', 'ld'], yrs) > 0)
