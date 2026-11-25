# Run after `npm run build`: python3 scripts/verify/switzerland.py
# Independent check of every figure on /population/switzerland/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'CHE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
p9 = next(yr for yr in range(1950, 2101) if P(I, yr) >= 9e6); p8 = next(yr for yr in range(1950, 2101) if P(I, yr) >= 8e6); assert p9 == y and P(I, y) < 9.05e6
assert sorted(countries(y, 5e6, EUROPE), key=lambda k: -P(k, y) / P(k, 1950))[0] == I
mig = sum(K(I, yr, 'NetMigrations') for yr in range(2000, 2024)); nat = sum(K(I, yr, 'NatChange') for yr in range(2000, 2024)); part = mig / (mig + nat) * 100; assert 75 < part < 85
falls = [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0]; assert falls == [1975, 1976, 1977] and all(K(I, yr, 'NetMigrations') < 0 for yr in falls)
assert sorted(countries(y, 5e6, EUROPE), key=lambda k: -f(k, y, 'LEx'))[0] == I and sorted(countries(y, 5e6), key=lambda k: -f(k, y, 'LEx'))[:4] == ['HKG', 'JPN', 'KOR', I]
assert next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0) == 2028 and all(F(yr, 'NatChange') < 0 for yr in range(2028, 2101))
assert all(F(yr, 'TFR') < 2.1 for yr in range(1971, 2101)) and P(I, 2100) > P(I, y)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'times 1950': f"{P(I, y) / P(I, 1950):.2f} times", 'pop 1950': m(P(I, 1950)), '8 million year': str(p8), '9 million year': str(p9),
 'migration 2000-2023': m(mig), 'natural 2000-2023': k1(nat), 'migration share': f"{round(part)}%", 'migration (thousand)': k1(K(I, y, 'NetMigrations')), 'natural increase': c(K(I, y, 'NatChange')),
 'lost 1974-1977': k1(P(I, 1974) - P(I, 1977)), 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE 2100': f"{F(2100,'LEx'):.1f}",
 'peak year': str(peak), 'peak': m(P(I, peak)), 'pop 2100': m(P(I, 2100)), 'tfr': f"{F(y,'TFR'):.2f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]),
}
sys.exit(run('switzerland', I, exp, ['population (millions)', 'peak year', 'LE', '9 million year'], yrs) > 0)
