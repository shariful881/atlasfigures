# Run after `npm run build`: python3 scripts/verify/united-states.py
# Independent check of every figure on /country/united-states/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'USA'; y = 2026; U = urban(I)
F = lambda yr, col: f(I, yr, col)
mig = K(I, y, 'NetMigrations'); ch = K(I, y, 'PopChange')
yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
first_nat_neg = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
boom = max(range(1946, 1965), key=lambda yr: F(yr, 'TFR') if yr in raw[I] else -1)
below = next(yr for yr in range(1965, 2101) if F(yr, 'TFR') < 2.1)
ranks = [(yr, rank(I, yr)) for yr in range(1951, 2101)]
slips = [yr for (yr, r), (_, r0) in zip(ranks, [(1950, rank(I, 1950))] + ranks) if r != r0]
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)),
 'share of world': p1(P(I, y) / P('WORLD', y) * 100), 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (millions)': m(ch),
 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land area': c(land(I)) + ' km²',
 'median age': f"{F(y,'MedianAgePop'):.1f}", 'median 1970': f"{F(1970,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr 1980': f"{F(1980,'TFR'):.2f}", 'tfr 2050': f"{F(2050,'TFR'):.2f}", 'boom year': str(boom), 'boom tfr': f"{F(boom,'TFR'):.2f}",
 'below 2.1 since': str(below), 'births 1961': m(K(I, 1961, 'Births')),
 'urban': p1(U[y]), 'births': m(K(I, y, 'Births')), 'deaths': m(K(I, y, 'Deaths')), 'natural (thousand)': f"{round(K(I,y,'NatChange')/1000):,} thousand",
 'net migrants (millions)': m(mig), 'migration share': p1(mig / ch * 100), 'natural 1960': m(K(I, 1960, 'NatChange')), 'migration 1960 (thousand)': f"{round(K(I,1960,'NetMigrations')/1000)} thousand",
 'deaths > births from': str(first_nat_neg), 'pop 2050': m(P(I, 2050)), 'pop 2100': m(P(I, 2100)),
 'LE 2019': f"{F(2019,'LEx'):.1f}", 'LE 2020': f"{F(2020,'LEx'):.1f}", 'LE 2021': f"{F(2021,'LEx'):.1f}", 'LE 2023': f"{F(2023,'LEx'):.1f}", 'LE now': f"{F(y,'LEx'):.1f}",
 'LE drop': f"{F(2019,'LEx')-F(2021,'LEx'):.1f} years", 'slip years': ', '.join(map(str, slips)) if False else str(slips[0]), 'slip 2': str(slips[1]), 'slip 3': str(slips[2]),
 'rank 2100': ordn(rank(I, 2100)),
}
sys.exit(run('united-states', I, exp, ['population (millions)', 'migration share', 'net migrants (millions)', 'tfr', 'median age', 'pop 2100', 'pop 2050', 'rank 2100', 'below 2.1 since'], yrs) > 0)
