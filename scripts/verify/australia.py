# Run after `npm run build`: python3 scripts/verify/australia.py
# Independent check of every figure on /country/australia/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'AUS'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
landrank = sorted([k for k in raw if k != 'WORLD'], key=lambda k: -land(k)).index(I) + 1
sparse = sorted([k for k in raw if k != 'WORLD' and P(k, y) > 20e6], key=lambda k: f(k, y, 'PopDensity'))
tpeak = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR'))
sub = next(yr for yr in range(1962, 2101) if F(yr, 'TFR') < 2.1)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': f"{round(ch/1000)} thousand", 'per day': c(ch / 365),
 'density': f"{F(y,'PopDensity'):.1f}", 'land': c(land(I)) + ' km²', 'land rank': ordn(landrank), 'least dense >20M': sparse[0] == I and '20 million' or 'NO',
 'natural (thousand)': f"{round(K(I,y,'NatChange')/1000)} thousand", 'migration (thousand)': f"{round(K(I,y,'NetMigrations')/1000)} thousand",
 'migration share': p1(F(y, 'NetMigrations') / F(y, 'PopChange') * 100), 'mig 2019': f"{round(K(I,2019,'NetMigrations')/1000)} thousand",
 'mig 2020': f"{round(K(I,2020,'NetMigrations')/1000)} thousand", 'mig 2022': f"{round(K(I,2022,'NetMigrations')/1000)} thousand", 'growth 2020': p1(F(2020, 'PopGrowthRate')),
 'urban': p1(U[y]), 'tfr': f"{F(y,'TFR'):.2f}", 'tfr peak': f"{F(tpeak,'TFR'):.2f}", 'tfr peak year': str(tpeak), 'below 2.1 since': str(sub),
 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}",
 'pop 1950': f"{P(I,1950)/1e6:.1f}M", 'rank 1950': ordn(rank(I, 1950)), 'pop 2050': m(P(I, 2050)), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
}
sys.exit(run('australia', I, exp, ['population (millions)', 'density', 'growth', 'migration share', 'pop 2100', 'pop 2050', 'LE', 'rank 2100'], yrs) > 0)
