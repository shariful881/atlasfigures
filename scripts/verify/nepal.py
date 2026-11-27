# Run after `npm run build`: python3 scripts/verify/nepal.py
# Independent check of every figure on /country/nepal/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y])}
I = 'NPL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
ch = K(I, y, 'PopChange'); nat = K(I, y, 'NatChange'); mig = K(I, y, 'NetMigrations')
assert sorted(countries(y, 1e6), key=lambda k: K(k, y, 'NetMigrations') / P(k, y))[0] == I and 0.85 < -mig / nat < 0.9 and ch > 0
assert [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0] == [2022, 2023]
otop = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert otop == 2023
assert all(F(yr, 'NetMigrations') > 0 for yr in (2019, 2020, 2021)) and all(F(yr, 'NetMigrations') < 0 for yr in range(2022, 2101))
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101))
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nl = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0)
assert sorted(countries(y, 0, {'5501'}), key=lambda k: -P(k, y)).index(I) == 5
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(ch / 365), 'natural (thousand)': k1(nat), 'departures (thousand)': k1(-mig), 'gain (thousand)': k1(ch), 'net migration (full)': c(mig),
 'outflow record': f"{k1(-K(I, otop, 'NetMigrations'))} in {otop}", 'ratio': f"{mf(I):.1f}", 'ratio 1950': f"{mf(I, 1950):.1f}", 'ratio 2100': f"{mf(I, 2100):.1f}",
 'tfr max': f"{F(tmax,'TFR'):.2f} children in {tmax}", 'below 2.1': f"2.1 in {below}", 'tfr': f"{F(y,'TFR'):.2f}", 'births peak': f"{btop} at about {k1(K(I, btop, 'Births'))}", 'births': k1(K(I, y, 'Births')),
 'peak': f"{m(P(I, peak))} around {peak}", 'natural loss': str(nl), 'pop 2100': m(P(I, 2100)), 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
}
sys.exit(run('nepal', I, exp, ['population (millions)', 'growth'], yrs) > 0)
