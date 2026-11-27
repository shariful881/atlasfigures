# Run after `npm run build`: python3 scripts/verify/mexico.py
# Independent check of every figure on /country/mexico/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'MEX'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
big = [k for k in raw if k != 'WORLD' and P(k, y) > 50e6]
drop = lambda k: f(k, 2019, 'LEx') - min(f(k, 2020, 'LEx'), f(k, 2021, 'LEx'))
sub = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR'))
bpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'Births')); opeak = min(range(1950, 2024), key=lambda yr: F(yr, 'NetMigrations'))
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); fall = next(yr for yr in range(2027, 2101) if F(yr, 'PopChange') < 0)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (millions)': m(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'biggest LE drop >50M': max(big, key=drop) == I and 'over 50 million' or 'NO', 'LE 2019': f"{F(2019,'LEx'):.1f}", 'LE 2020': f"{F(2020,'LEx'):.1f}", 'LE 2021': f"{F(2021,'LEx'):.1f}",
 'LE drop': f"{F(2019,'LEx')-F(2021,'LEx'):.1f} years", 'LE 2023': f"{F(2023,'LEx'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'below 2.1 from': str(sub), 'tfr': f"{F(y,'TFR'):.2f}",
 'tfr max': f"{F(tmax,'TFR'):.2f}", 'tfr max year': str(tmax), 'births peak': m(K(I, bpeak, 'Births')), 'births peak year': str(bpeak), 'births': m(K(I, y, 'Births')),
 'net out (thousand)': f"{round(-K(I,y,'NetMigrations')/1000)} thousand", 'out peak year': str(opeak), 'out peak': f"{round(-K(I,opeak,'NetMigrations')/1000)} thousand",
 'natural': m(K(I, y, 'NatChange')), 'peak': m(P(I, peak)), 'peak year': str(peak), 'first fall': str(fall), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
}
sys.exit(run('mexico', I, exp, ['population (millions)', 'LE drop', 'tfr', 'peak year', 'growth', 'change (millions)', 'births', 'births peak', 'LE 2019', 'LE 2021', 'LE', 'first fall', 'pop 2100', 'peak'], yrs) > 0)
