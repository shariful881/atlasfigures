# Run after `npm run build`: python3 scripts/verify/south-korea.py
# Independent check of every figure on /population/south-korea/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'KOR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
lower = sorted(k for k in raw if k != 'WORLD' and f(k, y, 'TFR') < F(y, 'TFR'))
low = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR'))
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
sub = next(yr for yr in range(1961, 2101) if F(yr, 'TFR') < 2.1)
nat = next(yr for yr in range(1961, 2101) if F(yr, 'NatChange') < 0)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'fall %': p1(-F(y, 'PopGrowthRate')), 'fall (thousand)': f"{round(-ch/1000)} thousand", 'per day': c(-ch / 365),
 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²', 'only HKG/MAC lower': lower == ['HKG', 'MAC'] and 'Hong Kong and Macao' or 'OTHERS LOWER',
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr low': f"{F(low,'TFR'):.2f}", 'low year': str(low), 'tfr 1960': f"{F(1960,'TFR'):.2f}", 'below 2.1 since': str(sub),
 'births': c(K(I, y, 'Births')), 'births 1960': m(K(I, 1960, 'Births')), 'deaths (thousand)': f"{round(K(I,y,'Deaths')/1000)} thousand",
 'deaths per birth': f"{F(y,'Deaths')/F(y,'Births'):.1f} for every birth", 'nat loss since': str(nat), 'peak': m(P(I, peak)), 'peak year': str(peak),
 'pop 2050': m(P(I, 2050)), 'pop 2100': m(P(I, 2100)), 'share kept': p1(P(I, 2100) / P(I, y) * 100), 'rank 2100': ordn(rank(I, 2100)),
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1970': f"{F(1970,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'urban': p1(U[y]),
}
sys.exit(run('south-korea', I, exp, ['population (millions)', 'tfr', 'tfr low', 'peak', 'fall (thousand)', 'deaths (thousand)', 'pop 2050', 'median 2050', 'pop 2100', 'LE'], yrs) > 0)
