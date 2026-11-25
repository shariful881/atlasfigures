# Run after `npm run build`: python3 scripts/verify/france.py
# Independent check of every figure on /population/france/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'FRA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
eur = {r['ISO3_code'] for r in []}
more = next(yr for yr in range(2027, 2101) if F(yr, 'NatChange') < 0)
later = [P(I, yr) for yr in range(2026, 2101)]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
ov = {k: P(k, y) for k in ['REU', 'GLP', 'MTQ', 'GUF', 'MYT']}
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr 2010': f"{F(2010,'TFR'):.2f}", 'births drop': p1((1 - F(y, 'Births') / F(2010, 'Births')) * 100),
 'births (thousand)': f"{round(K(I,y,'Births')/1000)} thousand", 'births 2010 (thousand)': f"{round(K(I,2010,'Births')/1000)} thousand", 'deaths (thousand)': f"{round(K(I,y,'Deaths')/1000)} thousand",
 'more deaths from': str(more), 'natural (hundreds)': c(round(K(I, y, 'NatChange') / 100) * 100), 'migration (thousand)': f"{round(K(I,y,'NetMigrations')/1000)} thousand",
 'low': m(min(later)), 'high': m(max(later)), 'peak year': str(peak), 'pop 2100': m(P(I, 2100)),
 'Réunion': f"{round(ov['REU']/1000)} thousand", 'Guadeloupe': f"({round(ov['GLP']/1000)} thousand)", 'Martinique': f"({round(ov['MTQ']/1000)} thousand)",
 'French Guiana': f"({round(ov['GUF']/1000)} thousand)", 'Mayotte': f"({round(ov['MYT']/1000)} thousand)", 'overseas sum': m(sum(ov.values())),
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'urban': p1(U[y]), 'rank 1950': ordn(rank(I, 1950)),
}
sys.exit(run('france', I, exp, ['population (millions)', 'tfr', 'tfr 2010', 'births drop', 'births (thousand)', 'births 2010 (thousand)', 'deaths (thousand)', 'pop 2100', 'overseas sum', 'growth'], yrs) > 0)
