# Run after `npm run build`: python3 scripts/verify/united-arab-emirates.py
# Independent check of every figure on /country/united-arab-emirates/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
I = 'ARE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
mf = lambda k, yr=2026: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
ch = K(I, y, 'PopChange'); times = P(I, y) / P(I, 1950)
assert sorted(countries(y), key=lambda k: -P(k, y) / P(k, 1950))[0] == I and 150 < times < 160
assert sorted(countries(y, 1e6), key=lambda k: -mf(k))[:2] == ['QAT', I] and 170 < mf(I) < 180 and mf(I, 2000) > mf(I) > mf(I, 2050)
cdr = K(I, y, 'Deaths') / P(I, y) * 1000; assert sorted(countries(y, 1e6), key=lambda k: K(k, y, 'Deaths') / P(k, y))[0] == I and cdr < 1 and 10 < K(I, y, 'Births') / K(I, y, 'Deaths') < 11
below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert below == 2006 and all(F(yr, 'TFR') < 2.1 for yr in range(2006, 2101))
assert K(I, y, 'NatChange') > K(I, y, 'NetMigrations') > 0
surge = max(range(1950, 2024), key=lambda yr: K(I, yr, 'PopChange')); assert surge == 2007 == max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations'))
assert [yr for yr in range(1950, 2101) if K(I, yr, 'PopChange') < 0] == [2019] and K(I, 2019, 'NetMigrations') < 0
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'density 2100': c(F(2100, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'times': f"{round(times)}-fold", 'times (headline)': f"{round(times)} times", 'pop 1950': k1(P(I, 1950)), 'pop 2000': m(P(I, 2000)), 'pop 2010': m(P(I, 2010)),
 'surge growth': p1(F(surge, 'PopGrowthRate')), 'surge gain': k1(K(I, surge, 'PopChange')), 'surge migration': k1(K(I, surge, 'NetMigrations')), '2019 fall': k1(-K(I, 2019, 'PopChange')),
 'deaths': k1(K(I, y, 'Deaths')), 'births': k1(K(I, y, 'Births')), 'migration': k1(K(I, y, 'NetMigrations')), 'below 2.1 since': str(below), 'tfr': f"{F(y,'TFR'):.2f}",
 'ratio': f"{mf(I):.1f}", 'ratio (rounded)': f"{round(mf(I))} males", 'ratio 2000': f"{mf(I, 2000):.1f}", 'ratio 2050': f"{mf(I, 2050):.1f}",
 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)), 'urban': p1(U[y]), 'median': f"{F(y,'MedianAgePop'):.1f}",
}
sys.exit(run('united-arab-emirates', I, exp, ['population (millions)', 'pop 1950', 'times (headline)', 'surge gain', 'surge migration', '2019 fall', 'ratio'], yrs) > 0)
