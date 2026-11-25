# Run after `npm run build`: python3 scripts/verify/sweden.py
# Independent check of every figure on /population/sweden/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'SWE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr))
neg = [yr for yr in range(1950, y) if F(yr, 'NatChange') < 0]; assert neg == [1997, 1998, 1999, 2000, 2001] and all(F(yr, 'NatChange') < 0 for yr in range(y, 2101))
assert [yr for yr in range(1950, 2101) if F(yr, 'NetMigrations') <= 0] == [1972, 1973]
mtop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); p10 = next(yr for yr in range(1950, 2101) if P(I, yr) >= 10e6); assert p10 == mtop + 1
assert P(I, 2100) > P(I, y)
grow = sorted(countries(y, 5e6, EUROPE), key=lambda k: -P(k, 2100) / P(k, y)); assert grow.index(I) == 1
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); blow = min(range(1992, 2005), key=lambda yr: K(I, yr, 'Births'))
assert sorted(countries(y, 10e6, EUROPE), key=lambda k: f(k, y, 'PopDensity'))[:2] == ['RUS', I]
assert sorted(countries(1950, 5e6), key=lambda k: -f(k, 1950, 'LEx'))[:2] == ['NLD', I]
assert sorted(countries(y, 0, {'924'}), key=lambda k: -P(k, y))[:2] == ['GBR', I]
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': k1(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'density 2100': c(F(2100, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'deaths': c(K(I, y, 'Deaths')), 'births': c(K(I, y, 'Births')), 'gap': c(-K(I, y, 'NatChange')), 'migration (thousand)': k1(K(I, y, 'NetMigrations')),
 'migration record year': str(mtop), 'migration record': k1(K(I, mtop, 'NetMigrations')), '10 million year': str(p10),
 'births peak': c(K(I, btop, 'Births')), 'births peak year': str(btop), 'births low': c(K(I, blow, 'Births')), 'births low year': str(blow), 'births 2010': c(K(I, 2010, 'Births')), 'tfr 2010': f"{F(2010,'TFR'):.2f}", 'tfr': f"{F(y,'TFR'):.2f}",
 'peak year': str(peak), 'peak (subtitle)': m(P(I, peak)), 'pop 2100': m(P(I, 2100)), 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE': f"{F(y,'LEx'):.1f}", 'LE 2100': f"{F(2100,'LEx'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'urban': p1(U[y]),
}
sys.exit(run('sweden', I, exp, ['population (millions)', 'peak year', 'pop 2100', 'deaths', 'births', '10 million year', 'migration record'], yrs) > 0)
