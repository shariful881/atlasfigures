# Run after `npm run build`: python3 scripts/verify/iraq.py
# Independent check of every figure on /population/iraq/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y])}
I = 'IRQ'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
W = countries(y, 0, {'922'})
cross = next(yr for yr in range(1950, 2101) if P(I, yr) > P('TUR', yr)); assert cross == 2067
assert all(sorted(W, key=lambda k: -P(k, yr))[:2] == ['YEM', I] for yr in range(2067, 2101)) and sorted(W, key=lambda k: -P(k, y))[:2] == ['TUR', I]
tpk = max(range(1950, 2101), key=lambda yr: P('TUR', yr)); assert 2040 <= tpk < 2050
ch = K(I, y, 'PopChange'); assert 950e3 < ch < 1e6 and K(I, y, 'NatChange') > ch and 8.4 < P(I, y) / P(I, 1950) < 8.6
dbl = next(yr for yr in range(1950, 2101) if P(I, yr) >= 2 * P(I, y)); assert all(K(I, yr, 'PopChange') > 0 for yr in range(2027, 2101))
falls = [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0]; assert falls == [1990, 2006, 2007] and all(F(yr, 'NetMigrations') < 0 for yr in falls)
otop = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
assert sorted(countries(y, 1e6, {'922'}), key=lambda k: f(k, y, 'MedianAgePop')).index(I) == 2
dec = {yr: P(I, yr) - P(I, yr - 10) for yr in range(1960, 2101, 10)}; assert max(dec, key=dec.get) == 2020 and abs(dec[2020] / 1e6 - 11) < 0.2
assert abs(U[y] / U[1950] - 2) < 0.05
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(ch / 365), 'change (thousand)': k1(ch), 'births': m(K(I, y, 'Births')), 'deaths': k1(K(I, y, 'Deaths')), 'pop 1950': m(P(I, 1950)),
 'cross': str(cross), 'pop 2050': m(P(I, 2050)), 'rank 2050': ordn(rank(I, 2050)), 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)), 'double': f"in {dbl}",
 'tfr max': f"{F(tmax,'TFR'):.2f} children per woman at its {tmax} high", 'tfr': f"{F(y,'TFR'):.2f}", 'below 2.1': f"only in {below}",
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'outflow record': f"{otop}, about {m(-K(I, otop, 'NetMigrations'))}", 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]),
}
sys.exit(run('iraq', I, exp, ['population (millions)', 'cross', 'pop 2100', 'births'], yrs) > 0)
