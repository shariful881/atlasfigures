# Run after `npm run build`: python3 scripts/verify/spain.py
# Independent check of every figure on /country/spain/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'ESP'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
assert all(K(I, yr, 'PopChange') < 0 for yr in range(peak + 1, 2101))
boom = max(range(1950, 2024), key=lambda yr: K(I, yr, 'PopChange')); assert boom == max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations'))
dip = [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0]; assert dip == [2012, 2013, 2014, 2015] and all(K(I, yr, 'NetMigrations') < 0 for yr in dip)
assert min(dip, key=lambda yr: K(I, yr, 'NetMigrations')) == 2013 and all(K(I, yr, 'NetMigrations') > 0 for yr in range(2016, 2024))
assert next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0) == 2015 and all(F(yr, 'NatChange') < 0 for yr in range(2015, 2101))
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); tlow = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR'))
assert K(I, y, 'Births') < K(I, btop, 'Births') / 2
le = sorted(countries(y, 5e6, EUROPE), key=lambda k: -f(k, y, 'LEx')); assert le[:3] == ['CHE', 'ITA', 'ESP']
lowW = sorted(countries(y, 5e6), key=lambda k: f(k, y, 'TFR')); assert lowW.index(I) < 15
south = sorted(countries(y, 0, {'925'}), key=lambda k: -P(k, y)); assert south[:2] == ['ITA', I]
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'fall': p1(-F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'per day': c(-ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'peak year': str(peak), 'peak': m(P(I, peak)), 'boom year': str(boom), 'boom migration': k1(K(I, boom, 'NetMigrations')), 'boom gain': k1(K(I, boom, 'PopChange')),
 'gain 2000-2010': m(P(I, 2010) - P(I, 2000)), 'emigration 1950': k1(-K(I, 1950, 'NetMigrations')), 'outflow 2013': k1(-K(I, 2013, 'NetMigrations')),
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr low': f"{F(tlow,'TFR'):.2f}", 'tfr low year': str(tlow), 'births': k1(K(I, y, 'Births')), 'births 1964': k1(K(I, btop, 'Births')), 'deaths': k1(K(I, y, 'Deaths')),
 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE 2100': f"{F(2100,'LEx'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
 'pop 2100': m(P(I, 2100)), 'back to': str(back), 'rank 2100': ordn(rank(I, 2100)), 'urban': p1(U[y]),
}
sys.exit(run('spain', I, exp, ['population (millions)', 'peak year', 'pop 2100', 'boom migration', 'boom gain', 'outflow 2013', 'LE', 'LE 1950', 'fall'], yrs) > 0)
