# Run after `npm run build`: python3 scripts/verify/ethiopia.py
# Independent check of every figure on /population/ethiopia/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
I = 'ETH'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
AF = countries(y, 0, AFRICA); assert sorted(AF, key=lambda k: -P(k, y))[:2] == ['NGA', I]
add = sorted(countries(y), key=lambda k: -K(k, y, 'PopChange')); assert add[:5] == ['IND', 'NGA', 'PAK', 'COD', I] and abs(K(I, y, 'NetMigrations')) < 0.02 * K(I, y, 'PopChange')
assert rank(I, 2050) == 7 == rank(I, 2100) and all(K(I, yr, 'PopChange') > 0 for yr in range(1950, 2101))
dbl = next(yr for yr in range(1950, 2101) if P(I, yr) >= 2 * P(I, y))
big = [k for k in countries(y, 10e6) if urban(k).get(y) is not None]; assert sorted(big, key=lambda k: urban(k)[y]).index(I) == 5 and U[y] < 25
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
assert 5 < K(I, y, 'Births') / K(I, y, 'Deaths') < 5.5 and 7.8 < P(I, y) / P(I, 1950) < 7.9
exp = exp_base(I, y, U) | {
 'change (millions)': m(K(I, y, 'PopChange')), 'births': m(K(I, y, 'Births')), 'deaths': k1(K(I, y, 'Deaths')), 'pop 1950': m(P(I, 1950)), 'double': f"by {dbl}",
 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'below 2.1': f"until {below}",
 'pop 2050': m(P(I, 2050)), 'rank 2050': ordn(rank(I, 2050)), 'pop 2100': m(P(I, 2100)), 'LE 1950': f"{F(1950,'LEx'):.1f} years (1950)",
}
sys.exit(run('ethiopia', I, exp, ['population (millions)', 'change (millions)', 'pop 2050'], yrs) > 0)
