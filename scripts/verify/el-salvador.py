# Run after `npm run build`: python3 scripts/verify/el-salvador.py
# Independent check of every figure on /country/el-salvador/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SLV'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/el-salvador.json'))['tableYears']
lac = countries(y, 1e6, {'915', '916', '931'}); main = countries(y, 1e6, {'916', '931'})
assert max(main, key=lambda k: f(k, y, 'PopDensity')) == I and sorted(lac, key=lambda k: -f(k, y, 'PopDensity'))[:3] == ['HTI', 'PRI', I]
assert sorted(countries(y, 1e6, {'916'}), key=lambda k: -f(k, y, 'PopDensity'))[:2] == [I, 'GTM']
NM = lambda yr: K(I, yr, 'NetMigrations'); assert all(NM(yr) < 0 for yr in R) and min(R, key=NM) == 1998
assert F(1980, 'LEx') < F(1979, 'LEx') - 5 and sorted(lac, key=lambda k: SR(k, y))[:2] == ['PRI', I]
assert next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2015 and all(F(yr, 'TFR') < 2.1 for yr in range(2015, 2101))
assert [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == [2006] and max(R, key=lambda yr: P(I, yr)) == 2047 and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1992
exp = exp_base(I, y, U) | {
 'gtm': f"against {c(f('GTM', y, 'PopDensity'))} in Guatemala", 'mig': f"{c(-NM(1980))} in 1980, {c(-NM(1998))} in 1998 (the most) and {c(-NM(y))} in 2026",
 'le': f"A fall from {F(1979, 'LEx'):.1f} years in 1979 to {F(1980, 'LEx'):.1f} in 1980", 'le82': f"with {F(1982, 'LEx'):.1f} still recorded for 1982", 'sr': f"Men are fewer: {SR(I, y):.1f} of them",
 'pk': f"carries it up to {m(P(I, 2047))} by 2047, after which it declines, to {m(P(I, 2100))} in 2100",
 'ld': f"1998, when departures topped arrivals by {c(-NM(1998))}",
}
sys.exit(run('el-salvador', I, exp, ['population (millions)', 'ld'], yrs) > 0)
