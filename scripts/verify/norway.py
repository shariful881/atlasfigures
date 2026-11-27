# Run after `npm run build`: python3 scripts/verify/norway.py
# Independent check of every figure on /country/norway/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101); EST = range(1950, 2024)
I = 'NOR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/norway.json'))['tableYears']
E5 = countries(y, 5e6, EUROPE)
assert sorted(sorted(E5, key=lambda k: f(k, y, 'PopDensity'))[:3]) == ['FIN', I, 'RUS']
assert sorted(E5, key=lambda k: -f(k, y, 'LEx'))[:4] == ['CHE', 'ITA', 'ESP', I]
assert all(F(yr, 'NetMigrations') > F(yr, 'NatChange') for yr in range(2021, y + 1)) and F(2020, 'NetMigrations') < F(2020, 'NatChange')
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0); assert peak == 2050 and nd == 2036 and all(F(yr, 'NatChange') < 0 for yr in range(nd, 2101))
tmax = max(R, key=lambda yr: F(yr, 'TFR')); tlow = min(EST, key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101))
nz = next(yr for yr in range(y + 1, 2101) if P('NZL', yr) > P(I, yr)); assert nz == 2063 and all(P('NZL', yr) > P(I, yr) for yr in range(nz, 2101))
assert 1.70 < P(I, y) / P(I, 1950) < 1.76
assert F(1970, 'NetMigrations') < 0 and all(F(yr, 'NetMigrations') > 0 for yr in yrs if yr >= 1980)
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(K(I, y, 'PopChange') / 365), 'net mig': k1(K(I, y, 'NetMigrations')), 'nat': k1(K(I, y, 'NatChange')),
 'growth 2022': f"{p1(F(2022,'PopGrowthRate'))} in 2022", 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'LE 1950': f"{F(1950,'LEx'):.1f} in 1950", 'LE 2050': f"{F(2050,'LEx'):.1f}",
 'tfr max': f"{tmax} high of {F(tmax,'TFR'):.2f}", 'below': f"2.1 in {below}", 'tfr low': f"{F(tlow,'TFR'):.2f}, in {tlow}", 'nd': f"From {nd}",
 'peak': f"{m(P(I, peak))} around {peak}", 'pop 2100': m(P(I, 2100)), 'nz': f"Norway in {nz}", 'peak (m)': m(P(I, peak)),
}
sys.exit(run('norway', I, exp, ['population (millions)', 'LE', 'peak (m)', 'pop 2100'], yrs) > 0)
