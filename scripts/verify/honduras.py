# Run after `npm run build`: python3 scripts/verify/honduras.py
# Independent check of every figure on /country/honduras/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'HND'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/honduras.json'))['tableYears']
L1 = countries(y, 1e6, {'915', '916', '931'})
assert sorted(L1, key=lambda k: -P(k, y) / P(k, 1950))[0] == I and 7 < P(I, y) / P(I, 1950) < 7.3
assert sorted(countries(y, 0, {'916'}), key=lambda k: -P(k, y))[:3] == ['MEX', 'GTM', I]
assert F(1998, 'LEx') < F(1997, 'LEx') - 5 < F(1999, 'LEx') - 5 and sorted(countries(1998), key=lambda k: f(k, 1998, 'LEx') - f(k, 1997, 'LEx'))[:3] == ['SSD', 'ERI', I] and K(I, 1998, 'Deaths') > 1.4 * K(I, 1997, 'Deaths')
bt = max(R, key=lambda yr: K(I, yr, 'Births')); tm = max(R, key=lambda yr: F(yr, 'TFR')); r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert (bt, tm, r21) == (2025, 1954, 2043)
assert sorted(L1, key=lambda k: f(k, y, 'MedianAgePop'))[:3] == ['GTM', 'HTI', I] and all(K(I, yr, 'NetMigrations') < 0 for yr in R)
pk = max(R, key=lambda yr: P(I, yr)); nn = next(yr for yr in R if K(I, yr, 'NatChange') < 0); assert (pk, nn) == (2090, 2090); half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 2008
exp = exp_base(I, y, U) | {
 'le98': f"from {F(1997, 'LEx'):.1f} to {F(1998, 'LEx'):.1f}, while deaths rose from {c(K(I, 1997, 'Deaths'))} to {c(K(I, 1998, 'Deaths'))}", 'le99': f"back to {F(1999, 'LEx'):.1f}", 'le74': f"to {F(1974, 'LEx'):.1f} in 1974",
 'mig': f"A small net outflow, {c(-K(I, y, 'NetMigrations'))} people this year", 'nat': f"natural increase of {c(K(I, y, 'NatChange'))}",
 'births': f"{c(K(I, bt, 'Births'))} births in {bt}, the series high", 'tfr': f"{F(tm, 'TFR'):.2f} in {tm} against {F(y, 'TFR'):.2f} today, with 2.1 crossed in {r21}",
 'pk': f"Late, in {pk}, at {m(P(I, pk))}", 'urb': f"larger group since {half}; they make up {p1(U[y])} now, rising to {p1(U[2050])} by 2050", '1950': f"against {m(P(I, 1950))} in 1950",
 'ld': f"deaths rise from {c(K(I, 1997, 'Deaths'))} to {c(K(I, 1998, 'Deaths'))}",
}
sys.exit(run('honduras', I, exp, ['population (millions)', 'ld'], yrs) > 0)
