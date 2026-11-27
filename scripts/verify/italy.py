# Run after `npm run build`: python3 scripts/verify/italy.py
# Independent check of every figure on /country/italy/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'ITA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
assert all(K(I, yr, 'PopChange') < 0 for yr in range(peak + 1, 2101)), 'not smaller every year after peak'
old = sorted(countries(y, 5e6), key=lambda k: -f(k, y, 'MedianAgePop')); assert old[:2] == ['JPN', 'ITA']
oldEu = sorted(countries(y, 5e6, EUROPE), key=lambda k: -f(k, y, 'MedianAgePop')); assert oldEu[0] == 'ITA'
low = sorted(countries(y, 5e6, EUROPE), key=lambda k: f(k, y, 'TFR')); assert low[:2] == ['UKR', 'ITA']
fall = sorted(countries(y, 20e6), key=lambda k: P(k, 2100) / P(k, y)); assert fall.index(I) == 5
south = sorted(countries(y, 0, {'925'}), key=lambda k: -P(k, y)); assert south[0] == I
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births'))
nat1 = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
negs = sum(1 for yr in range(1993, 2024) if F(yr, 'NatChange') < 0); assert negs >= 25
mig = K(I, y, 'NetMigrations'); nat = K(I, y, 'NatChange'); assert 0 < mig < -nat / 4
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': k1(-ch), 'per day': c(-ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'peak year': str(peak), 'peak': m(P(I, peak)), 'deaths per birth': f"about {K(I,y,'Deaths')/K(I,y,'Births'):.1f} deaths", 'first natural loss': str(nat1),
 'migration (thousand)': k1(mig), 'natural loss (thousand)': k1(-nat), 'births 1964 over 1 million': 'more than 1 million births in ' + str(btop) if K(I, btop, 'Births') > 1e6 else 'NO',
 'births (thousand)': k1(K(I, y, 'Births')), 'deaths (thousand)': k1(K(I, y, 'Deaths')), 'tfr': f"{F(y,'TFR'):.2f}", 'tfr 1964': f"{F(btop,'TFR'):.2f}",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'pop 2100': m(P(I, 2100)), 'fall %': p1((1 - P(I, 2100) / P(I, y)) * 100),
 'rank 2100': ordn(rank(I, 2100)), 'urban': p1(U[y]),
}
sys.exit(run('italy', I, exp, ['population (millions)', 'peak year', 'births (thousand)', 'deaths (thousand)', 'tfr', 'median', 'pop 2100', 'fall %', 'rank 2100'], yrs) > 0)
