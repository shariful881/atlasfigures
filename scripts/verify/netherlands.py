# Run after `npm run build`: python3 scripts/verify/netherlands.py
# Independent check of every figure on /population/netherlands/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'NLD'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
d = lambda k, yr=y: f(k, yr, 'PopDensity')
assert sorted(countries(y, 10e6, EUROPE), key=lambda k: -d(k))[0] == I and sorted(countries(y, 10e6), key=lambda k: -d(k)).index(I) == 4
mig = K(I, y, 'NetMigrations'); assert 0.9 < mig / ch < 1 and F(y, 'NatChange') > 0
mtop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations'))
p18 = next(yr for yr in range(1950, 2101) if P(I, yr) >= 18e6); assert p18 == mtop + 1
nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); assert F(y, 'TFR') < F(tmax, 'TFR') / 2
west = sorted(countries(y, 0, {'926'}), key=lambda k: -P(k, y)); assert west[:3] == ['DEU', 'FRA', I]
U10 = {k: urban(k).get(y) for k in countries(y, 10e6)}; urb = sorted([k for k in U10 if U10[k] is not None], key=lambda k: -U10[k]); assert urb.index(I) < 10 and U[y] > 95
assert 0.94 * P(I, y) < P(I, 2100) < P(I, y)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': k1(ch), 'per day': c(ch / 365), 'density': c(d(I)), 'density 1950': c(d(I, 1950)), 'density peak': c(d(I, peak)), 'land': c(land(I)) + ' km²',
 'migration (thousand)': k1(mig), 'migration record year': str(mtop), 'migration record': k1(K(I, mtop, 'NetMigrations')), '18 million year': str(p18),
 'peak year': str(peak), 'peak': m(P(I, peak)), 'natural loss from': str(nat), 'pop 2100': m(P(I, 2100)),
 'tfr max': f"{F(tmax,'TFR'):.2f}", 'tfr max year': str(tmax), 'tfr': f"{F(y,'TFR'):.2f}", 'LE': f"{F(y,'LEx'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'urban': p1(U[y]),
}
sys.exit(run('netherlands', I, exp, ['population (millions)', 'density', 'peak year', 'peak', 'pop 2100', 'growth', '18 million year'], yrs) > 0)
