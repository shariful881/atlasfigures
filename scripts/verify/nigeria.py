# Run after `npm run build`: python3 scripts/verify/nigeria.py
# Independent check of every figure on /country/nigeria/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'NGA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
africa = [r for r in []]
import gzip, csv
pass_idn = next(yr for yr in range(1950, 2101) if P(I, yr) > P('IDN', yr)); pass_usa = next(yr for yr in range(1950, 2101) if P(I, yr) > P('USA', yr))
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); ufrom = next(yr for yr in sorted(U) if U[yr] and U[yr] > 50)
more_births = sorted(k for k in raw if k != 'WORLD' and f(k, y, 'Births') > F(y, 'Births'))
lowest_le = min((k for k in raw if k != 'WORLD'), key=lambda k: f(k, y, 'LEx'))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'births': m(K(I, y, 'Births')), 'deaths': m(K(I, y, 'Deaths')), 'natural': m(K(I, y, 'NatChange')), 'births/day': c(round(K(I, y, 'Births') / 365 / 1000) * 1000),
 'only IND/CHN more births': more_births == ['CHN', 'IND'] and 'Only India and China' or 'NO', 'tfr': f"{F(y,'TFR'):.2f}", 'tfr max': f"{F(tmax,'TFR'):.2f}",
 'tfr max year': str(tmax), 'tfr 2050': f"{F(2050,'TFR'):.2f}", 'pass IDN': str(pass_idn), 'pass USA': str(pass_usa), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
 'lowest LE': lowest_le == I and 'lower figure' or 'NO', 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE 2000': f"{F(2000,'LEx'):.1f}", 'IMR': f"{F(y,'IMR'):.1f}",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'urban from': str(ufrom),
}
sys.exit(run('nigeria', I, exp, ['population (millions)', 'births', 'median', 'pass USA', 'pass IDN', 'tfr', 'tfr max', 'tfr 2050', 'pop 2100', 'median 2050'], yrs) > 0)
