# Run after `npm run build`: python3 scripts/verify/saudi-arabia.py
# Independent check of every figure on /population/saudi-arabia/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
I = 'SAU'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
mf = lambda k, yr=2026: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
assert 20 < P(I, y) / P(I, 1950) < 21 and peak == 2100 and all(K(I, yr, 'PopChange') > 0 for yr in range(2027, 2101)) and 2 < P(I, 2100) / P(I, y) < 2.05
big = sorted(countries(y, 1e6), key=lambda k: -mf(k)); assert big.index(I) == 5 and set(big[:5]) == {'QAT', 'ARE', 'OMN', 'BHR', 'KWT'} and 145 < mf(I) < 155
falls = [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0]; assert falls == [2017, 2018] and all(K(I, yr, 'NetMigrations') < -900e3 for yr in falls)
reb = max(range(1950, 2024), key=lambda yr: K(I, yr, 'PopChange')); assert reb == 2022 and K(I, reb, 'NetMigrations') > 950e3
below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert below == 2034
assert K(I, y, 'NatChange') > 4 * K(I, y, 'NetMigrations')
assert sorted(countries(y, 0, {'922'}), key=lambda k: -P(k, y))[:4] == ['TUR', 'IRQ', 'YEM', I]
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank number': f'number {rank(I, y)} on the world list', 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'pop 1950': m(P(I, 1950)), 'pop 2000': m(P(I, 2000)), 'births': k1(K(I, y, 'Births')), 'deaths': k1(K(I, y, 'Deaths')),
 'men per 100 women': f"{round(mf(I))} males", 'ratio 2026': f"{mf(I):.1f}", 'ratio 1950': f"{mf(I, 1950):.1f}", 'ratio 2100': f"{mf(I, 2100):.1f}",
 'rebound': m(K(I, reb, 'PopChange')), 'tfr 1970': f"{F(1970,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}", 'below 2.1': str(below), 'median': f"{F(y,'MedianAgePop'):.1f}",
 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)), 'urban': p1(U[y]),
}
sys.exit(run('saudi-arabia', I, exp, ['population (millions)', 'pop 1950', 'men per 100 women', 'rebound', 'tfr 1970', 'pop 2100', 'below 2.1'], yrs) > 0)
