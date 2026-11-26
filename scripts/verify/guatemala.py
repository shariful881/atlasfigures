# Run after `npm run build`: python3 scripts/verify/guatemala.py
# Independent check of every figure on /population/guatemala/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'GTM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/guatemala.json'))['tableYears']
LAT = {'915', '916', '931'}; CAM = {'916'}; L1 = countries(y, 1e6, LAT)
assert sorted(L1, key=lambda k: f(k, y, 'MedianAgePop'))[:4] == [I, 'HTI', 'HND', 'BOL'] and max(L1, key=lambda k: f(k, 2000, 'TFR') - f(k, y, 'TFR')) == I
under = next(yr for yr in R if F(yr, 'TFR') < 2.1); tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert (under, tmax) == (2032, 1957)
assert all(K(I, yr, 'NetMigrations') < 0 for yr in range(1964, 2101)) and K(I, 1963, 'NetMigrations') >= 0; out = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 2000
assert sorted(countries(y, 0, CAM), key=lambda k: -P(k, y))[:2] == ['MEX', I] and sorted(countries(y, 1e6, CAM), key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['SLV', I]
ut = max(range(1950, 1980), key=lambda yr: U[yr]); ul = min(range(1970, 2001), key=lambda yr: U[yr]); ub = next(yr for yr in range(ul + 1, 2051) if U[yr] > U[ut]); half = next(yr for yr in R if U.get(yr) and U[yr] > 50)
assert (ut, ul, ub, half) == (1973, 1981, 1996, 2008)
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2077 and next(yr for yr in range(2020, 2101) if F(yr, 'LEx') > F(2019, 'LEx')) == 2023
exp = exp_base(I, y, U) | {
 'tfr': f"a rate of {F(1990, 'TFR'):.2f} in 1990 and {F(2000, 'TFR'):.2f} in 2000, compared with {F(y, 'TFR'):.2f} today", 'under': f"under 2.1 only from {under}",
 'median': f"under {F(2000, 'MedianAgePop'):.1f} in 2000; the median is {F(y, 'MedianAgePop'):.1f} now and {F(2050, 'MedianAgePop'):.1f} in the 2050 projection",
 'mig': f"net loss is close to {k1(-K(I, y, 'NetMigrations'))}", 'out': f"most of all in {out} (near {k1(-K(I, out, 'NetMigrations'))})", 'births': f"{k1(K(I, y, 'Births'))} babies expected against {k1(K(I, y, 'Deaths'))} deaths",
 'urban': f"it was {p1(U[ut])} in {ut}, then only {p1(U[ul])} by {ul}, and was higher again only in {ub}", 'half': f"majority since {half} and make up {p1(U[y])} today",
 'peak': f"high in {pk} with {m(P(I, pk))}; by 2100 it is a little lower, at {m(P(I, 2100))}", 'times': f"about {P(I, y) / P(I, 1950):.1f}-fold",
 'le': f"slipped from {F(2019, 'LEx'):.1f} in 2019 to {F(2021, 'LEx'):.1f} in 2021", 'ld': f"growth stops in {pk} at {m(P(I, pk))}, and 2100 finishes at {m(P(I, 2100))}",
}
sys.exit(run('guatemala', I, exp, ['population (millions)', 'ld'], yrs) > 0)
