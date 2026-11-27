# Run after `npm run build`: python3 scripts/verify/mali.py
# Independent check of every figure on /country/mali/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'MLI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/mali.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); WAF = {'914'}
assert sorted(countries(1950), key=lambda k: f(k, 1950, 'LEx')).index(I) == 3 and F(y, 'LEx') > 2 * F(1950, 'LEx')
assert all(K(I, yr, 'NetMigrations') < 0 for yr in R); mig = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert mig == 2012
assert sorted(B, key=lambda k: f(k, y, 'MedianAgePop')).index(I) == 4
assert sorted(countries(y, 0, WAF), key=lambda k: -land(k))[:2] == ['NER', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert (tmax, under) == (1980, 2099)
fifty = next(yr for yr in R if P(I, yr) > 5e7); assert fifty == 2055
rise = lambda k: rank(k, y) - rank(k, 2100); assert max(rise(k) for k in B) == rise(I) == 27
assert sorted(countries(2100, 0, WAF), key=lambda k: -P(k, 2100)).index(I) == 3 and U[2050] < 50
exp = exp_base(I, y, U) | {
 'le 1950': f"The 1950 estimate, {F(1950, 'LEx'):.1f} years", 'le now': f"the {y} figure is {F(y, 'LEx'):.1f}", 'le 2000': f"{F(2000, 'LEx'):.1f}",
 'imr': f"from {F(1950, 'IMR'):.1f} deaths per thousand births to {F(y, 'IMR'):.1f}", 'tfr': f"{F(y, 'TFR'):.2f} now against {F(tmax, 'TFR'):.2f} at its {tmax} high",
 'mig top': f"The heaviest estimated year is {mig}, near {k1(-K(I, mig, 'NetMigrations'))}", 'mig now': f"around {k1(-K(I, y, 'NetMigrations'))} this year",
 'nat': f"the {k1(K(I, y, 'NatChange'))} by which births exceed deaths", 'fifty': f"{fifty}. The medium projection carries on to {m(P(I, 2100))} in 2100",
 'rank 2100': f"Mali then {ordn(rank(I, 2100))} globally", 'rise': f"its {rise(I)}-place rise from {ordn(rank(I, y))} today", 'times': f"already {P(I, y) / P(I, 1950):.1f} times",
 'under': f"reaches 2.1 only in {under}", 'urban 1950': f"from {p1(U[1950])} in 1950 to {p1(U[y])}", 'urban 2050': f"the 2050 projection, {p1(U[2050])}",
}
sys.exit(run('mali', I, exp, ['population (millions)', 'median'], yrs) > 0)
