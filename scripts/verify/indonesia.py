# Run after `npm run build`: python3 scripts/verify/indonesia.py
# Independent check of every figure on /population/indonesia/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'IDN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
sub = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR'))
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100)); ufrom = next(yr for yr in sorted(U) if U[yr] and U[yr] > 50)
passed = [(yr, k) for yr in range(2027, 2101) for k in raw if k not in ('WORLD', I) and P(k, yr) > P(I, yr) and P(k, yr - 1) <= P(I, yr - 1)]
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (millions)': m(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')),
 'land': c(land(I)) + ' km²', 'land (millions)': m(land(I)) + ' km²', 'tfr': f"{F(y,'TFR'):.2f}", 'below 2.1 from': str(sub), 'tfr max': f"{F(tmax,'TFR'):.2f}", 'tfr max year': str(tmax),
 'peak year': str(peak), 'peak': m(P(I, peak)), 'first fall': str(peak + 1), 'nat loss from': str(nat), 'pop 2100': m(P(I, 2100)), 'back to': str(back),
 'passed': ', '.join(f'{k} {yr}' for yr, k in passed) == 'PAK 2037, NGA 2040, COD 2072, ETH 2078' and '2072' or 'NO', 'rank 2100': ordn(rank(I, 2100)),
 'pop 1950': m(P(I, 1950)), 'median': f"{F(y,'MedianAgePop'):.1f}", 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'urban from': str(ufrom),
 'IMR 1950': str(round(F(1950, 'IMR'))), 'IMR': f"{F(y,'IMR'):.1f}",
}
sys.exit(run('indonesia', I, exp, ['population (millions)', 'peak year', 'tfr', 'peak', 'first fall', 'nat loss from', 'growth', 'change (millions)', 'tfr max'], yrs) > 0)
