# Run after `npm run build`: python3 scripts/verify/japan.py
# Independent check of every figure on /country/japan/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'JPN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
nat = next(yr for yr in range(2001, 2101) if F(yr, 'NatChange') < 0)
under = next(yr for yr in range(peak + 1, 2101) if P(I, yr) < 100e6)
big = sorted([k for k in raw if k != 'WORLD' and P(k, y) > 1e6], key=lambda k: -f(k, y, 'MedianAgePop'))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'fall (millions)': m(-ch), 'fall %': p1(-F(y, 'PopGrowthRate')), 'per day': c(-ch / 365),
 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²', 'peak year': str(peak), 'peak': m(P(I, peak)), 'lost': m(P(I, peak) - P(I, y)),
 'deaths': m(K(I, y, 'Deaths')), 'births': m(K(I, y, 'Births')), 'births (thousand)': f"{round(K(I,y,'Births')/1000)} thousand", 'ratio': f"{F(y,'Deaths')/F(y,'Births'):.1f} to one",
 'births 1973': m(K(I, 1973, 'Births')), 'births 1950': m(K(I, 1950, 'Births')), 'tfr': f"{F(y,'TFR'):.2f}", 'nat loss since': str(nat),
 'oldest >1M': big[0] == I and 'more than a million' or 'NOT OLDEST', 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}",
 'median 1980': f"{F(1980,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}",
 'LE 2100': f"{F(2100,'LEx'):.1f}", 'IMR': f"{F(y,'IMR'):.1f}", 'migration (thousand)': f"{round(K(I,y,'NetMigrations')/1000)} thousand",
 'migration cover': p1(F(y, 'NetMigrations') / -F(y, 'NatChange') * 100), 'natural loss (thousand)': f"{round(-K(I,y,'NatChange')/1000)} thousand",
 'pop 2100': m(P(I, 2100)), 'pop 1950': m(P(I, 1950)), 'under 100M': str(under), 'rank 1950': ordn(rank(I, 1950)), 'rank 2100': ordn(rank(I, 2100)), 'urban': p1(U[y]),
}
sys.exit(run('japan', I, exp, ['population (millions)', 'deaths', 'births', 'migration (thousand)', 'fall %', 'births (thousand)', 'births 1973', 'median', 'pop 2100', 'under 100M', 'LE', 'peak year'], yrs) > 0)
