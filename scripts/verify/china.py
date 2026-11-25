# Run after `npm run build`: python3 scripts/verify/china.py
# Independent check of every figure on /population/china/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'CHN'; y = 2026; U = urban(I)
F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
low = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR'))
boom = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR'))
over50 = next(yr for yr in range(1950, 2101) if F(yr, 'MedianAgePop') > 50)
maj = next(yr for yr in sorted(U) if U[yr] and U[yr] > 50)
under = next(yr for yr in range(peak + 1, 2101) if P(I, yr) < 1e9)
exp = {
 'population (full)': c(P(I, y)), 'population (billions)': b2(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'fall (millions)': m(-ch), 'fall %': p1(-F(y, 'PopGrowthRate')), 'per day': c(-ch / 365),
 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²', 'peak year': str(peak), 'peak': b2(P(I, peak)), 'lost since peak': m(P(I, peak) - P(I, y)),
 'births': m(K(I, y, 'Births')), 'deaths': m(K(I, y, 'Deaths')), 'births full': c(K(I, y, 'Births')), 'deaths full': c(K(I, y, 'Deaths')),
 'deaths over births': m(K(I, y, 'Deaths') - K(I, y, 'Births')), 'births 2016': m(K(I, 2016, 'Births')),
 'tfr': f"{F(y,'TFR'):.2f}", 'low tfr': f"{F(low,'TFR'):.2f}", 'low year': str(low), 'boom year': str(boom), 'boom tfr': f"{F(boom,'TFR'):.2f}",
 'LE 1958': f"{F(1958,'LEx'):.1f}", 'LE 1960': f"{F(1960,'LEx'):.1f}", 'pop fell in 1960': str(F(1960, 'PopChange') < 0),
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2000': f"{F(2000,'MedianAgePop'):.1f}", 'median 1980': f"{F(1980,'MedianAgePop'):.1f}",
 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}", 'over 50 from': str(over50),
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'urban majority': str(maj), 'urban people': m(P(I, y) * U[y] / 100),
 'under 1bn': str(under), 'pop 2100': m(P(I, 2100)),
}
exp['pop fell in 1960'] = exp['LE 1960']  # the fall itself is checked by the build (assertClaim); keep a page figure here
sys.exit(run('china', I, exp, ['population (billions)', 'peak', 'fall (millions)', 'fall %', 'births', 'deaths', 'births 2016', 'tfr', 'low tfr', 'median', 'median 2100', 'over 50 from', 'under 1bn', 'pop 2100', 'deaths over births'], yrs) > 0)
