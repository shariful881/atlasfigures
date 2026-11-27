# Run after `npm run build`: python3 scripts/verify/germany.py
# Independent check of every figure on /country/germany/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'DEU'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
mig = sum(K(I, yr, 'NetMigrations') for yr in range(2010, 2024)); natl = sum(K(I, yr, 'NatChange') for yr in range(2010, 2024))
top = max(range(1950, 2024), key=lambda yr: F(yr, 'NetMigrations'))
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
sub = next(yr for yr in range(1965, 2101) if F(yr, 'TFR') < 2.1)
low = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR'))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'fall %': p1(-F(y, 'PopGrowthRate')), 'per day': c(-ch / 365),
 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²', 'deaths since': str(nat), 'deaths': m(K(I, y, 'Deaths')), 'births': m(K(I, y, 'Births')),
 'deaths per birth': f"{F(y,'Deaths')/F(y,'Births'):.2f}", 'migration 2010-23': m(mig), 'natural loss 2010-23': m(-natl), 'pop 2010': m(P(I, 2010)), 'pop 2023': m(P(I, 2023)),
 'top year': str(top), 'top inflow': m(K(I, top, 'NetMigrations')), 'peak year': str(peak), 'peak': m(P(I, peak)), 'pop 2050': m(P(I, 2050)), 'pop 2100': m(P(I, 2100)),
 'tfr': f"{F(y,'TFR'):.2f}", 'below 2.1 since': str(sub), 'tfr low': f"{F(low,'TFR'):.2f}", 'low year': str(low), 'tfr 1964': f"{F(1964,'TFR'):.2f}",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'urban': p1(U[y]), 'rank 1950': ordn(rank(I, 1950)),
}
sys.exit(run('germany', I, exp, ['population (millions)', 'deaths since', 'pop 2100', 'pop 2050', 'migration 2010-23', 'natural loss 2010-23', 'top inflow', 'fall %', 'peak year', 'tfr', 'tfr low'], yrs) > 0)
