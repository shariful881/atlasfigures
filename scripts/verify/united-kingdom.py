# Run after `npm run build`: python3 scripts/verify/united-kingdom.py
# Independent check of every figure on /population/united-kingdom/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'GBR'; y = 2026; U = urban(I)
F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); mig = K(I, y, 'NetMigrations'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
loss = [yr for yr in range(1950, 2024) if F(yr, 'NatChange') < 0]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
bpeak = max(range(1950, 2024), key=lambda yr: F(yr, 'Births'))
sub = next(yr for yr in range(1965, 2101) if F(yr, 'TFR') < 2.1)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'median': f"{F(y,'MedianAgePop'):.1f}", 'tfr': f"{F(y,'TFR'):.2f}", 'urban': p1(U[y]),
 'births': c(K(I, y, 'Births')), 'deaths': c(K(I, y, 'Deaths')), 'margin': c(K(I, y, 'NatChange')), 'births (thousand)': f"{round(K(I,y,'Births')/1000)} thousand",
 'deaths (thousand)': f"{round(K(I,y,'Deaths')/1000)} thousand", 'loss years': f"{loss[0]} and {loss[1]}", 'from': str(y + 1),
 'net migration (thousand)': f"{round(mig/1000)} thousand", 'migration 2022': f"{round(K(I,2022,'NetMigrations')/1000)} thousand", 'migration share': p1(mig / ch * 100),
 'peak': m(P(I, peak)), 'peak year': str(peak), 'pop 2100': m(P(I, 2100)), 'births peak year': str(bpeak), 'births peak': m(K(I, bpeak, 'Births')),
 'tfr 1964': f"{F(1964,'TFR'):.2f}", 'below 2.1 from': str(sub), 'rank 1950': ordn(rank(I, 1950)), 'pop 1950': m(P(I, 1950)),
 'added since 1950': m(P(I, y) - P(I, 1950)), 'rank 2050': ordn(rank(I, 2050)), 'rank 2100': ordn(rank(I, 2100)),
}
sys.exit(run('united-kingdom', I, exp, ['population (millions)', 'rank', 'births (thousand)', 'deaths (thousand)', 'net migration (thousand)', 'migration 2022', 'peak', 'peak year', 'pop 2100', 'density', 'births peak'], yrs) > 0)
