# Run after `npm run build`: python3 scripts/verify/tanzania.py
# Independent check of every figure on /population/tanzania/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
I = 'TZA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
mult = P(I, 2100) / P(I, y); ms = sorted(countries(y, 20e6), key=lambda k: -P(k, 2100) / P(k, y)); assert ms.index(I) == 2 and sorted(ms[:2]) == ['AGO', 'COD']
assert rank(I, 2100) == 9 and rank(I, 2050) == 15 and all(K(I, yr, 'PopChange') > 0 for yr in range(1950, 2101))
pe = next(yr for yr in range(2027, 2101) if P(I, yr) > P('EGY', yr)); assert pe == 2071
dbl = next(yr for yr in range(1950, 2101) if P(I, yr) >= 2 * P(I, y))
assert sorted(countries(y), key=lambda k: -K(k, y, 'PopChange')).index(I) == 7 and K(I, y, 'PopChange') > 2e6
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); assert tmax == 1974 and all(F(yr, 'TFR') > 2.1 for yr in range(1950, 2101))
assert sorted(countries(y, 0, {'910'}), key=lambda k: -P(k, y))[:2] == ['ETH', I] and 9.4 < P(I, y) / P(I, 1950) < 9.6 and 6 < K(I, y, 'Births') / K(I, y, 'Deaths') < 6.2
exp = exp_base(I, y, U) | {
 'pop 2100': m(P(I, 2100)), 'mult': f"{mult:.1f} times", 'rank 2050': ordn(rank(I, 2050)), 'rank 2100': ordn(rank(I, 2100)), 'pass Egypt': str(pe),
 'change (millions)': m(K(I, y, 'PopChange')), 'births': m(K(I, y, 'Births')), 'pop 1950': m(P(I, 1950)), 'double': f"by {dbl}",
 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'tfr 2100': f"{F(2100,'TFR'):.2f} in 2100", 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]),
}
sys.exit(run('tanzania', I, exp, ['population (millions)', 'pop 2100', 'mult', 'pass Egypt'], yrs) > 0)
