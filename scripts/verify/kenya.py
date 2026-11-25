# Run after `npm run build`: python3 scripts/verify/kenya.py
# Independent check of every figure on /population/kenya/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
I = 'KEN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); fall = F(1980, 'TFR') - F(y, 'TFR')
AF10 = countries(y, 10e6, AFRICA); assert sorted(AF10, key=lambda k: -(f(k, 1980, 'TFR') - f(k, y, 'TFR')))[:2] == ['RWA', I] and F(y, 'TFR') < F(1980, 'TFR') / 2
below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); assert peak == 2098 and P(I, 2100) < P(I, peak) and 10 < P(I, y) / P(I, 1950) < 10.3
ug = next(yr for yr in range(2027, 2101) if P('UGA', yr) > P(I, yr)); assert ug == 2046
assert sorted(countries(y, 0, {'910'}), key=lambda k: -P(k, y))[:3] == ['ETH', 'TZA', I]
assert all(F(yr, 'NetMigrations') < 0 for yr in range(2010, y + 1)) and F(y, 'PopGrowthRate') < min(f('UGA', y, 'PopGrowthRate'), f('TZA', y, 'PopGrowthRate'))
exp = exp_base(I, y, U) | {
 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'tfr 1980': f"{F(1980,'TFR'):.2f} in 1980", 'fall': f"{fall:.2f}-child", 'below 2.1': f"2.1 in {below}",
 'change (millions)': m(K(I, y, 'PopChange')), 'pop 1950': m(P(I, 1950)), 'uganda passes': str(ug), 'peak': f"{m(P(I, peak))} around {peak}",
 'pop 2050': m(P(I, 2050)), 'rank 2050': ordn(rank(I, 2050)), 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]),
}
sys.exit(run('kenya', I, exp, ['population (millions)', 'tfr', 'pop 2050'], yrs) > 0)
