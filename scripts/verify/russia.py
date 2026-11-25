# Run after `npm run build`: python3 scripts/verify/russia.py
# Independent check of every figure on /population/russia/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'RUS'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); pos = [yr for yr in range(peak + 1, 2101) if F(yr, 'NatChange') >= 0]
under = next(yr for yr in range(peak + 1, 2101) if P(I, yr) < 140e6); men = F(y, 'TPopulationMale1July') / F(y, 'TPopulationFemale1July') * 100
low = min(range(1981, 2024), key=lambda yr: F(yr, 'LEx')); tlow = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR'))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'fall %': p1(-F(y, 'PopGrowthRate')), 'per day': c(-ch / 365), 'density': f"{F(y,'PopDensity'):.1f}",
 'land': c(land(I)) + ' km²', 'land (millions)': m(land(I)) + ' km²', 'peak': m(P(I, peak)), 'peak year': str(peak), 'below peak': m(P(I, peak) - P(I, y)),
 'births>deaths years': f"{pos[0]}–{pos[-1]}" if pos == list(range(2012, 2017)) else 'NO', 'natural (thousand)': f"{round(-K(I,y,'NatChange')/1000)} thousand",
 'migration (thousand)': f"{round(K(I,y,'NetMigrations')/1000)} thousand", 'men per 100': f"{men:.1f}", 'men 1950': f"{F(1950,'TPopulationMale1July')/F(1950,'TPopulationFemale1July')*100:.1f}",
 'women excess': m((F(y, 'TPopulationFemale1July') - F(y, 'TPopulationMale1July')) * 1000), 'LE 1990': f"{F(1990,'LEx'):.1f}", 'LE low': f"{F(low,'LEx'):.1f}", 'LE low year': str(low),
 'LE 2021': f"{F(2021,'LEx'):.1f}", 'LE 2019': f"{F(2019,'LEx'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'births 1987': m(K(I, 1987, 'Births')), 'births 1999': m(K(I, 1999, 'Births')),
 'tfr low': f"{F(tlow,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}", 'births': m(K(I, y, 'Births')), 'urban': p1(U[y]), 'rank 1950': ordn(rank(I, 1950)), 'rank 2100': ordn(rank(I, 2100)),
 'pop 2100': m(P(I, 2100)), 'under 140M': str(under), 'median': f"{F(y,'MedianAgePop'):.1f}",
}
sys.exit(run('russia', I, exp, ['population (millions)', 'men per 100', 'pop 2100', 'peak', 'below peak', 'LE', 'LE low', 'under 140M', 'rank 2100'], yrs) > 0)
