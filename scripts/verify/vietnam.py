# Run after `npm run build`: python3 scripts/verify/vietnam.py
# Independent check of every figure on /population/vietnam/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'VNM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
h = next(yr for yr in range(1950, 2101) if P(I, yr) >= 100e6); span = [F(yr, 'TFR') for yr in range(1998, 2024)]
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
bpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'Births'))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': f"{round(ch/1000)} thousand", 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 '100M year': str(h), 'pop 1950': m(P(I, 1950)), 'births': m(K(I, y, 'Births')), 'deaths (thousand)': f"{round(K(I,y,'Deaths')/1000)} thousand",
 'tfr low 1998-2023': f"{min(span):.2f}", 'tfr high 1998-2023': f"{max(span):.2f}", 'tfr max': f"{F(tmax,'TFR'):.2f}", 'tfr max year': str(tmax), 'tfr 1990': f"{F(1990,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}",
 'peak': m(P(I, peak)), 'peak year': str(peak), 'nat loss': str(nat), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2000': f"{F(2000,'MedianAgePop'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
 'median 2100': f"{F(2100,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]),
 'births peak': m(K(I, bpeak, 'Births')), 'births peak year': str(bpeak),
}
sys.exit(run('vietnam', I, exp, ['population (millions)', '100M year', 'peak year', 'median 2050', 'peak', 'pop 2100', 'tfr', 'births', 'births peak'], yrs) > 0)
