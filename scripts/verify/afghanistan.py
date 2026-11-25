# Run after `npm run build`: python3 scripts/verify/afghanistan.py
# Independent check of every figure on /population/afghanistan/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y])}
I = 'AFG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
nonAf = [k for k in countries(y, 1e6) if raw[k][2026]['ParentID'] not in AFRICA]
assert sorted(nonAf, key=lambda k: f(k, y, 'MedianAgePop'))[0] == I and sorted(nonAf, key=lambda k: -f(k, y, 'TFR'))[0] == I
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); assert tmax == 1995
falls = [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0]; assert falls == [1979, 1980, 1981, 1982, 1986, 1987, 1990, 2000] and all(F(yr, 'NetMigrations') < 0 for yr in falls)
otop = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); itop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations'))
assert all(F(yr, 'NetMigrations') < 0 for yr in range(2021, y + 1)) and F(2020, 'NetMigrations') > 0
dbl = next(yr for yr in range(1950, 2101) if P(I, yr) >= 2 * P(I, y)); assert max(range(1950, 2101), key=lambda yr: P(I, yr)) == 2100 and 2.85 < P(I, 2100) / P(I, y) < 2.95
assert sorted(countries(y, 0, {'5501'}), key=lambda k: -P(k, y)).index(I) == 4 and 3.8 < K(I, y, 'Births') / K(I, 1950, 'Births') < 4
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(K(I, y, 'PopChange') / 365), 'change (millions)': m(K(I, y, 'PopChange')),
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'tfr': f"{F(y,'TFR'):.2f}", 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'births': m(K(I, y, 'Births')), 'births 1950': k1(K(I, 1950, 'Births')),
 'pop 1979': m(P(I, 1979)), 'pop 1983': m(P(I, 1983)), 'outflow record': f"{otop} alone was about {m(-K(I, otop, 'NetMigrations'))}", 'inflow record': f"{itop} shows a net inflow of about {m(K(I, itop, 'NetMigrations'))}",
 'double by': str(dbl), 'pop 2050': m(P(I, 2050)), 'rank 2050': ordn(rank(I, 2050)), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)), 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE': f"{F(y,'LEx'):.1f}",
}
sys.exit(run('afghanistan', I, exp, ['population (millions)', 'median', 'double by', 'pop 2100', 'rank 2100'], yrs) > 0)
