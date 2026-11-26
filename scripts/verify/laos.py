# Run after `npm run build`: python3 scripts/verify/laos.py
# Independent check of every figure on /population/laos/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'LAO'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/laos.json'))['tableYears']
sea = countries(y, 1e6, {'920'})
assert min(sea, key=lambda k: f(k, y, 'PopDensity')) == I
assert sorted(sea, key=lambda k: -f(k, y, 'IMR'))[:3] == ['TLS', 'MMR', I] and sorted(sea, key=lambda k: -P(k, y)).index(I) == 7
assert all(K(I, yr, 'NetMigrations') <= 0.5 for yr in R) and min(R, key=lambda yr: K(I, yr, 'NetMigrations')) == 2004
tm = max(R, key=lambda yr: F(yr, 'TFR')); rp = next(yr for yr in R if yr > y and F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); pk = max(R, key=lambda yr: P(I, yr))
assert (tm, rp, bt, pk) == (1983, 2035, 1993, 2068) and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 2037 and 4.6 < P(I, y) / P(I, 1950) < 4.9
exp = exp_base(I, y, U) | {
 'imr': f"{F(1950, 'IMR'):.1f} for every 1,000 births in 1950, {F(1990, 'IMR'):.1f} in 1990 and {F(y, 'IMR'):.1f} in 2026", 'le': f"from {F(1950, 'LEx'):.1f} to {F(y, 'LEx'):.1f} years",
 'tfr': f"{F(tm, 'TFR'):.2f} in 1983, {F(2000, 'TFR'):.2f} in 2000 and {F(y, 'TFR'):.2f} at present", 'b': f"2026 is expected to bring {c(K(I, y, 'Births'))}",
 'mig': f"The biggest net loss, {c(-K(I, 2004, 'NetMigrations'))}, falls in 2004; this year's is {c(-K(I, y, 'NetMigrations'))}", 'pk': f"2068, with {m(P(I, pk))}", 'end': f"leaving {m(P(I, 2100))} in 2100",
 'ld': f"The 1950 estimate is {F(1950, 'IMR'):.1f} per 1,000 births",
}
sys.exit(run('laos', I, exp, ['population (millions)', 'ld'], yrs) > 0)
