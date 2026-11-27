# Run after `npm run build`: python3 scripts/verify/nicaragua.py
# Independent check of every figure on /country/nicaragua/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NIC'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/nicaragua.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert all(NM(yr) < 0 for yr in R) and min(R, key=NM) == 2003
assert F(1972, 'LEx') < F(1971, 'LEx') - 5 < F(1973, 'LEx') - 5 and F(1979, 'LEx') < F(1977, 'LEx') - 5
lead = lambda yr: P(I, yr) > P('PRY', yr); assert [yr for yr in range(1951, 2101) if lead(yr) != lead(yr - 1)] == [1969, 1998, 2011, 2014, 2026, 2069] and abs(P(I, y) - P('PRY', y)) < 1e5
assert sorted(countries(y, 0, {'916'}), key=lambda k: -P(k, y)).index(I) == 3
tm = max(R, key=lambda yr: F(yr, 'TFR')); rp = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); pk = max(R, key=lambda yr: P(I, yr))
assert (tm, rp, bt, pk) == (1959, 2029, 1991, 2071) and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1977 and 5.2 < P(I, y) / P(I, 1950) < 5.4
exp = exp_base(I, y, U) | {
 'le': f"life expectancy is {F(1971, 'LEx'):.1f} years in 1971, {F(1972, 'LEx'):.1f} in 1972 and {F(1973, 'LEx'):.1f} in 1973", 'le2': f"({F(1978, 'LEx'):.1f}, then {F(1979, 'LEx'):.1f})",
 'mig': f"The biggest net loss came in 2003, at {c(-NM(2003))}; for 2026 the figure is {c(-NM(y))}", 'pk': f"Around 2071, at {m(P(I, pk))}; by 2100 the projection eases to {m(P(I, 2100))}",
 'b': f"peak of {c(K(I, bt, 'Births'))}, with {c(K(I, y, 'Births'))} expected", 'tfr': f"fertility, {F(tm, 'TFR'):.2f} in 1959, drops under 2.1 in 2029",
 'ld': f"with {c(-NM(2003))} more leaving than arriving",
}
sys.exit(run('nicaragua', I, exp, ['population (millions)', 'ld'], yrs) > 0)
