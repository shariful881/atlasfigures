# Run after `npm run build`: python3 scripts/verify/singapore.py
# Independent check of every figure on /population/singapore/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
I = 'SGP'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
assert sorted(countries(y, 1e6), key=lambda k: -f(k, y, 'PopDensity'))[0] == I and all(v == 100 for v in U.values() if v is not None)
assert sorted(countries(y, 1e6), key=lambda k: f(k, y, 'TFR')).index(I) == 4 and F(y, 'TFR') < 1 and all(F(yr, 'TFR') < 2.1 for yr in range(1975, 2101))
tlow = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR')); tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR'))
rise = F(2050, 'MedianAgePop') - F(y, 'MedianAgePop'); assert sorted(countries(y, 5e6), key=lambda k: -(f(k, 2050, 'MedianAgePop') - f(k, y, 'MedianAgePop')))[0] == I and 14 < rise < 15
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100))
falls = [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0]; assert falls == [2002, 2003, 2020, 2021] and all(K(I, yr, 'NetMigrations') < 0 for yr in falls) and min(falls, key=lambda yr: K(I, yr, 'PopChange')) == 2020
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births'))
assert sorted(countries(y, 0, {'920'}), key=lambda k: -f(k, y, 'LEx'))[0] == I
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'density 1950': c(F(1950, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr low': f"{F(tlow,'TFR'):.2f}", 'tfr low year': str(tlow), 'tfr 1956': f"{F(tmax,'TFR'):.2f} in {tmax}",
 'births': k1(K(I, y, 'Births')), 'births peak': f"peaked in {btop} at {k1(K(I, btop, 'Births'))}",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}", 'rise': f"about {round(rise)} years", 'LE': f"{F(y,'LEx'):.1f}",
 '2020 fall': k1(-K(I, 2020, 'PopChange')), 'natural increase': k1(K(I, y, 'NatChange')),
 'peak year': str(peak), 'peak': m(P(I, peak)), 'natural loss': str(nat), 'pop 2100': m(P(I, 2100)), 'back to': str(back), 'urban': p1(U[y]),
}
sys.exit(run('singapore', I, exp, ['population (millions)', 'density', 'peak year', 'peak', 'pop 2100', 'back to', 'tfr', 'median 2050'], yrs) > 0)
