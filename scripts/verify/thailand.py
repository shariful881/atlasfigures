# Run after `npm run build`: python3 scripts/verify/thailand.py
# Independent check of every figure on /country/thailand/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
I = 'THA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
assert peak == nat == 2022 and all(K(I, yr, 'PopChange') < 0 and F(yr, 'NatChange') < 0 for yr in range(2023, 2101))
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert K(I, y, 'Births') < K(I, btop, 'Births') / 2
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101))
assert sorted(countries(y, 0, {'920'}), key=lambda k: -f(k, y, 'MedianAgePop'))[0] == I and sorted(countries(y, 0, {'920'}), key=lambda k: -P(k, y))[:4] == ['IDN', 'PHL', 'VNM', I]
assert sorted(countries(y, 50e6), key=lambda k: P(k, 2100) / P(k, y))[:5] == ['KOR', 'CHN', 'ITA', 'JPN', I]
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': k1(-ch), 'per day': c(-ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'peak year': str(peak), 'peak': m(P(I, peak)), 'natural loss': k1(-K(I, y, 'NatChange')), 'migration': k1(K(I, y, 'NetMigrations')),
 'births peak': f"{btop} at about {m(K(I, btop, 'Births'))}", 'births': k1(K(I, y, 'Births')), 'deaths': k1(K(I, y, 'Deaths')), 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'below 2.1': f"2.1 in {below}", 'tfr': f"{F(y,'TFR'):.2f}",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}",
 'pop 2100': m(P(I, 2100)), 'fall': p1((1 - P(I, 2100) / P(I, y)) * 100), 'back to': str(back), 'rank 2050': ordn(rank(I, 2050)), 'rank 2100': ordn(rank(I, 2100)),
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]),
}
sys.exit(run('thailand', I, exp, ['population (millions)', 'peak year', 'pop 2100', 'peak', 'fall', 'births', 'deaths', 'rank 2100'], yrs) > 0)
