# Run after `npm run build`: python3 scripts/verify/canada.py
# Independent check of every figure on /population/canada/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'CAN'; y = 2026; U = urban(I)
F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); mig = K(I, y, 'NetMigrations'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
g7 = sorted(['USA', 'CAN', 'GBR', 'DEU', 'FRA', 'ITA', 'JPN'], key=lambda i: -f(i, y, 'PopGrowthRate'))
mpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'NetMigrations'))
nat_neg = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
tpeak = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR'))
sub = next(yr for yr in range(1961, 2101) if F(yr, 'TFR') < 2.1)
big = sorted([k for k in raw if k != 'WORLD' and P(k, y) > 30e6], key=lambda k: f(k, y, 'PopDensity'))
landrank = sorted([k for k in raw if k != 'WORLD'], key=lambda k: -land(k)).index(I) + 1
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density (1 dp)': f"{F(y,'PopDensity'):.1f}", 'land': c(land(I)) + ' km²',
 'land (millions)': m(land(I)) + ' km²', 'land rank': ordn(landrank), 'G7 fastest': g7[0] == 'CAN' and 'G7' or 'NOT FASTEST',
 'migration share': p1(mig / ch * 100), 'net migrants full': c(mig), 'net migrants (thousand)': f"{round(mig/1000)} thousand",
 'migration peak': f"{round(K(I,mpeak,'NetMigrations')/1000)} thousand", 'migration peak year': str(mpeak), 'growth 2023': p1(F(2023, 'PopGrowthRate')),
 'growth 2022 same rounding': p1(F(2022, 'PopGrowthRate')), 'births': c(K(I, y, 'Births')), 'deaths': c(K(I, y, 'Deaths')),
 'natural (thousand)': f"{round(K(I,y,'NatChange')/1000)} thousand", 'deaths > births from': str(nat_neg), 'pop 2100': m(P(I, 2100)),
 'least dense >30M': big[0] == 'CAN' and '30 million' or 'NOT LEAST DENSE', 'US times as dense': str(round(f('USA', y, 'PopDensity') / F(y, 'PopDensity'))),
 'urban': p1(U[y]), 'tfr': f"{F(y,'TFR'):.2f}", 'tfr US': f"{f('USA',y,'TFR'):.2f}", 'tfr peak': f"{F(tpeak,'TFR'):.2f}", 'tfr peak year': str(tpeak),
 'below 2.1 from': str(sub), 'median': f"{F(y,'MedianAgePop'):.1f}", 'median gap US': f"{F(y,'MedianAgePop')-f('USA',y,'MedianAgePop'):.1f} years",
 'median 1970': f"{F(1970,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}",
}
sys.exit(run('canada', I, exp, ['population (millions)', 'migration share', 'growth', 'growth 2023', 'net migrants (thousand)', 'migration peak', 'land (millions)', 'density (1 dp)', 'pop 2100', 'deaths > births from'], yrs) > 0)
