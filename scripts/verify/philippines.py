# Run after `npm run build`: python3 scripts/verify/philippines.py
# Independent check of every figure on /country/philippines/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'PHL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
big = sorted([k for k in raw if k != 'WORLD' and P(k, y) > 50e6], key=lambda k: -(f(k, 2010, 'TFR') - f(k, y, 'TFR')))
bpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'Births')); osince = next(s for s in range(1950, 2024) if all(F(k, 'NetMigrations') < 0 for k in range(s, 2024)))
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
ufrom = next(yr for yr in sorted(U) if U[yr] and U[yr] > 50)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'density 1950': c(F(1950, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'tfr 2010': f"{F(2010,'TFR'):.2f}", 'tfr 2020': f"{F(2020,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}", 'tfr 1950': f"{F(1950,'TFR'):.2f}",
 'fall rank 4, 3 African above': big[:4] == ['UGA', 'NGA', 'ETH', 'PHL'] and 'all African' or 'NO', 'births': m(K(I, y, 'Births')), 'deaths (thousand)': f"{round(K(I,y,'Deaths')/1000)} thousand",
 'natural': m(K(I, y, 'NatChange')), 'out (thousand)': f"{round(-K(I,y,'NetMigrations')/1000)} thousand", 'out since': str(osince), 'median': f"{F(y,'MedianAgePop'):.1f}",
 'births peak': str(bpeak), 'peak': m(P(I, peak)), 'peak year': str(peak), 'nat loss': str(nat), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
 'pop 1950': m(P(I, 1950)), 'urban': p1(U[y]), 'urban from': str(ufrom),
}
sys.exit(run('philippines', I, exp, ['population (millions)', 'tfr 2010', 'tfr', 'peak', 'peak year', 'pop 2100', 'out (thousand)', 'density', 'density 1950'], yrs) > 0)
