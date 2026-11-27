# Run after `npm run build`: python3 scripts/verify/state-of-palestine.py
# Independent check of every figure on /country/state-of-palestine/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'PSE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/state-of-palestine.json'))['tableYears']
assert raw[I][2026]['Location'] == 'State of Palestine'
D = lambda yr: K(I, yr, 'Deaths'); NM = lambda yr: K(I, yr, 'NetMigrations')
assert F(2023, 'LEx') < F(2022, 'LEx') - 10 and D(2023) > 2 * D(2022) and F(2024, 'LEx') > F(2023, 'LEx') and F(y, 'LEx') > F(2022, 'LEx')
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1966, 1967, 1968, 1969] and min(R, key=NM) == 1967
big1 = countries(y, 1e6); assert sorted(big1, key=lambda k: -f(k, y, 'PopDensity')).index(I) == 4
assert sorted(countries(y, 1e6, {'922'}), key=lambda k: f(k, y, 'MedianAgePop'))[:2] == ['YEM', I]
assert max(R, key=lambda yr: P(I, yr)) == 2100 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2064 and 5.9 < P(I, y) / P(I, 1950) < 6.1
exp = exp_base(I, y, U) | {
 'd': f"Estimated deaths go from {c(D(2022))} in 2022 to {c(D(2023))} in 2023", 'le': f"life expectancy from {F(2022, 'LEx'):.1f} to {F(2023, 'LEx'):.1f} years", 'le24': f"{F(2024, 'LEx'):.1f} for 2024",
 'out': f"the largest net outflow, {c(-NM(1967))}, is recorded for 1967", 'gap': f"There were {c(P(I, 1965) - P(I, 1969))} fewer people", 'fut': f"reaching {m(P(I, 2050))} in 2050; at the century's close the projection stands at {m(P(I, 2100))}",
 'ld': f"Estimated deaths rise from {c(D(2022))} in 2022 to {c(D(2023))} in 2023",
}
sys.exit(run('state-of-palestine', I, exp, ['population (millions)', 'ld'], yrs) > 0)
