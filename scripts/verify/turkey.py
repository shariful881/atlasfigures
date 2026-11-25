# Run after `npm run build`: python3 scripts/verify/turkey.py
# Independent check of every figure on /population/turkey/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'TUR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100)); last = max(yr for yr in range(1950, 2101) if F(yr, 'TFR') >= 2.1)
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); mtop = max(range(1950, 2024), key=lambda yr: F(yr, 'NetMigrations'))
osince = next(s for s in range(1950, 2024) if all(F(k, 'NetMigrations') < 0 for k in range(s, 2024)))
big = sorted([k for k in raw if k != 'WORLD' and P(k, y) > 50e6], key=lambda k: P(k, 2100) / P(k, y))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'peak': m(P(I, peak)), 'peak year': str(peak), 'nat loss': str(nat), 'pop 2100': m(P(I, 2100)), 'fall %': p1((1 - P(I, 2100) / P(I, y)) * 100), 'back to': str(back),
 'sixth steepest': big.index(I) == 5 and 'only five' or 'NO', 'rank 2100': ordn(rank(I, 2100)), 'births 2015': m(K(I, 2015, 'Births')), 'births': m(K(I, y, 'Births')),
 'last above 2.1': str(last), 'tfr last above': f"{F(last,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}", 'tfr max': f"{F(tmax,'TFR'):.2f}", 'tfr max year': str(tmax),
 'mig top': m(K(I, mtop, 'NetMigrations')), 'out since': str(osince), 'out (thousand)': f"{round(-K(I,y,'NetMigrations')/1000)} thousand",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'urban': p1(U[y]),
}
sys.exit(run('turkey', I, exp, ['population (millions)', 'peak year', 'pop 2100', 'peak', 'back to', 'tfr', 'tfr last above', 'births', 'births 2015', 'growth'], yrs) > 0)
