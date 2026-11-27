# Run after `npm run build`: python3 scripts/verify/paraguay.py
# Independent check of every figure on /country/paraguay/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'PRY'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/paraguay.json'))['tableYears']
lac = countries(y, 1e6, {'915', '916', '931'})
assert sorted(lac, key=lambda k: f(k, 2021, 'LEx') - f(k, 2019, 'LEx'))[:2] == ['BOL', I] and F(2022, 'LEx') > F(2021, 'LEx') + 3
assert SR(I, y) > 100 and sorted(lac, key=lambda k: -SR(k, y))[:2] == ['HND', I]
assert sorted(lac, key=lambda k: f(k, y, 'PopDensity'))[:3] == ['BOL', 'ARG', I] and sorted(lac, key=lambda k: -f(k, y, 'TFR')).index(I) == 3
assert all(P(I, yr) > P('NIC', yr) for yr in range(2014, 2026)) and P(I, y) < P('NIC', y) and next(yr for yr in range(y + 1, 2101) if P(I, yr) > P('NIC', yr)) == 2069
NM = lambda yr: K(I, yr, 'NetMigrations'); assert all(NM(yr) < 0 for yr in R) and min(R, key=NM) == 2007
rp = next(yr for yr in R if F(yr, 'TFR') < 2.1); pk = max(R, key=lambda yr: P(I, yr)); assert (rp, pk) == (2043, 2078) and P(I, 2100) > P(I, 2050)
assert next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1990 and 4.6 < P(I, y) / P(I, 1950) < 4.8
exp = exp_base(I, y, U) | {
 'le': f"{F(2019, 'LEx'):.1f} years in 2019, {F(2020, 'LEx'):.1f} in 2020, {F(2021, 'LEx'):.1f} in 2021, then {F(2022, 'LEx'):.1f} in 2022",
 'sr': f"the ratio is {SR(I, y):.1f}, counting men", 'mig': f"most of all in 2007 ({c(-NM(2007))})", 'pk': f"reaching {m(P(I, pk))}, with {m(P(I, 2100))} left in 2100", 'ma': f"under {F(y, 'MedianAgePop'):.1f}",
 'ld': f"It sank to {F(2021, 'LEx'):.1f} years from {F(2019, 'LEx'):.1f} in 2019",
}
sys.exit(run('paraguay', I, exp, ['population (millions)', 'ld'], yrs) > 0)
