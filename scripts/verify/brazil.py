# Run after `npm run build`: python3 scripts/verify/brazil.py
# Independent check of every figure on /country/brazil/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'BRA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100)); sub = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
bpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'Births'))
osince = next(s for s in range(1950, 2024) if all(F(k, 'NetMigrations') < 0 for k in range(s, 2024)))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'peak': m(P(I, peak)), 'peak year': str(peak), 'deaths from': str(nat), 'pop 2050': m(P(I, 2050)), 'pop 2100': m(P(I, 2100)), 'back to': str(back), 'rank 2100': ordn(rank(I, 2100)),
 'tfr 1950': f"{F(1950,'TFR'):.2f}", 'tfr 2000': f"{F(2000,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}", 'below 2.1 since': str(sub), 'births peak year': str(bpeak),
 'births peak': m(K(I, bpeak, 'Births')), 'births': m(K(I, y, 'Births')), 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}",
 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'LE 2019': f"{F(2019,'LEx'):.1f}", 'LE 2021': f"{F(2021,'LEx'):.1f}",
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'out since': str(osince), 'out (thousand)': f"{round(-K(I,y,'NetMigrations')/1000)} thousand",
 'natural (thousand)': f"{round(K(I,y,'NatChange')/1000)} thousand", 'gain (thousand)': f"{round(ch/1000)} thousand",
}
sys.exit(run('brazil', I, exp, ['population (millions)', 'peak year', 'tfr 1950', 'tfr', 'peak', 'pop 2050', 'pop 2100', 'back to', 'below 2.1 since', 'out since'], yrs) > 0)
