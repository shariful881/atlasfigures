# Run after `npm run build`: python3 scripts/verify/india.py
# Independent check of every figure on /population/india/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'IND'; y = 2026; U = urban(I)
F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
overtook = next(yr for yr in range(1950, 2101) if P(I, yr) > P('CHN', yr))
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
first_fall = next(yr for yr in range(2027, 2101) if F(yr, 'PopChange') < 0)
sub = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
bpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'Births'))
same = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100))
exp = {
 'population (full)': c(P(I, y)), 'population (billions)': b2(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (millions)': m(ch), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr 1960': f"{F(1960,'TFR'):.2f}", 'tfr desc': f"{F(y,'TFR'):.2f} children", 'below 2.1 from': str(sub),
 'overtook': str(overtook), 'lead now': m(P(I, y) - P('CHN', y)), 'lead 2050': m(P(I, 2050) - P('CHN', 2050)),
 'peak year': str(peak), 'peak': b2(P(I, peak)), 'first fall': str(first_fall), 'pop 2100': b2(P(I, 2100)), 'same size year': str(same),
 'births peak year': str(bpeak), 'births peak': m(K(I, bpeak, 'Births')), 'births now': m(K(I, y, 'Births')), 'births/day': c(round(K(I, y, 'Births') / 365 / 1000) * 1000),
 'IMR 1950': str(round(F(1950, 'IMR'))), 'IMR 2000': str(round(F(2000, 'IMR'))), 'IMR now': f"{F(y,'IMR'):.1f}",
 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE now': f"{F(y,'LEx'):.1f}", 'LE 2021': f"{F(2021,'LEx'):.1f}", 'LE 2019': f"{F(2019,'LEx'):.1f}",
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'urban people': m(P(I, y) * U[y] / 100),
}
sys.exit(run('india', I, exp, ['population (billions)', 'overtook', 'lead now', 'lead 2050', 'births/day', 'births now', 'growth', 'first fall', 'peak', 'pop 2100', 'urban', 'urban 2050', 'urban people', 'tfr desc'], yrs) > 0)
