# Run after `npm run build`: python3 scripts/verify/malaysia.py
# Independent check of every figure on /country/malaysia/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
I = 'MYS'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
mf = lambda k, yr=2026: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
ch = K(I, y, 'PopChange'); peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nat = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
share = K(I, y, 'NetMigrations') / ch * 100; assert 38 < share < 42
out = [yr for yr in range(1950, 2101) if F(yr, 'NetMigrations') < 0]; assert out == list(range(1952, 1980))
mtop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births'))
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101))
assert sorted(countries(y, 0, {'920'}), key=lambda k: -P(k, y)).index(I) == 5 and 5.8 < P(I, y) / P(I, 1950) < 6.2
assert all(F(yr, 'NetMigrations') > 0 for yr in range(nat, peak + 1)) and P(I, y) < P(I, 2100) < P(I, peak)
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (thousand)': k1(ch), 'per day': c(ch / 365), 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²',
 'natural (thousand)': k1(K(I, y, 'NatChange')), 'migration (thousand)': k1(K(I, y, 'NetMigrations')), 'migration share': f"roughly {round(share)}%", 'pop 1950': m(P(I, 1950)),
 'migration record': f"about {k1(K(I, mtop, 'NetMigrations'))}, in {mtop}", 'men per 100 women': f"{mf(I):.1f} per 100",
 'births peak': f"{btop}, at about {k1(K(I, btop, 'Births'))}", 'births': k1(K(I, y, 'Births')), 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'below 2.1': f"2.1 in {below}", 'tfr': f"{F(y,'TFR'):.2f}",
 'urban 1950': p1(U[1950]), 'urban': p1(U[y]), 'urban 2050': p1(U[2050]),
 'peak year': str(peak), 'peak': m(P(I, peak)), 'natural loss from': str(nat), 'pop 2100': m(P(I, 2100)), 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
}
sys.exit(run('malaysia', I, exp, ['population (millions)', 'growth', 'peak', 'peak year', 'urban', 'urban 1950', 'migration share'], yrs) > 0)
