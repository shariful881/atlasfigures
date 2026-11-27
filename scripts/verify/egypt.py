# Run after `npm run build`: python3 scripts/verify/egypt.py
# Independent check of every figure on /country/egypt/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'EGY'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
p200 = next(yr for yr in range(1950, 2101) if P(I, yr) >= 200e6); tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); sub = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (millions)': m(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'births/day': c(round(K(I, y, 'Births') / 365 / 100) * 100), 'pop 1950': m(P(I, 1950)), 'pop 2100': m(P(I, 2100)), 'pass 200M': str(p200),
 'urban 1980': p1(U[1980]), 'urban 2000': p1(U[2000]), 'urban': p1(U[y]), 'urban 2050': p1(U[2050]), 'tfr': f"{F(y,'TFR'):.2f}", 'tfr max': f"{F(tmax,'TFR'):.2f}", 'tfr max year': str(tmax),
 'tfr 2000': f"{F(2000,'TFR'):.2f}", 'below 2.1 from': str(sub), 'rank 2050': ordn(rank(I, 2050)), 'IMR 1950': str(round(F(1950, 'IMR'))), 'IMR 2000': str(round(F(2000, 'IMR'))),
 'IMR': f"{F(y,'IMR'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'growth 2050': p1(F(2050, 'PopGrowthRate')),
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
}
sys.exit(run('egypt', I, exp, ['population (millions)', 'growth', 'tfr', 'pass 200M', 'pop 2100', 'growth 2050', 'urban', 'urban 1980', 'urban 2050', 'median', 'median 2050'], yrs) > 0)
