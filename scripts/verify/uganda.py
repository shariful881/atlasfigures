# Run after `npm run build`: python3 scripts/verify/uganda.py
# Independent check of every figure on /country/uganda/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
I = 'UGA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
assert sorted(countries(y, 10e6, AFRICA), key=lambda k: -f(k, y, 'PopDensity'))[:4] == ['RWA', 'BDI', 'NGA', I]
assert 7 < K(I, y, 'Births') / K(I, y, 'Deaths') < 7.2 and sorted(countries(y, 10e6), key=lambda k: f(k, y, 'MedianAgePop')).index(I) < 10
pk = next(yr for yr in range(2027, 2101) if P(I, yr) > P('KEN', yr)); dbl = next(yr for yr in range(1950, 2101) if P(I, yr) >= 2 * P(I, y)); assert pk == 2046
assert 0 < F(2100, 'PopGrowthRate') < 0.05 and all(K(I, yr, 'PopChange') > 0 for yr in range(1950, 2101)) and max(range(1950, 2101), key=lambda yr: P('KEN', yr)) < 2100
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
itop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert itop == 2016 and all(F(yr, 'NetMigrations') > 0 for yr in range(2016, 2022)) and all(F(yr, 'NetMigrations') < 0 for yr in range(2022, 2101))
assert sorted(countries(y, 0, {'910'}), key=lambda k: -P(k, y)).index(I) == 3
exp = exp_base(I, y, U) | {
 'density 1950': c(F(1950, 'PopDensity')), 'density 2050': c(F(2050, 'PopDensity')), 'density 2100': c(F(2100, 'PopDensity')),
 'births': m(K(I, y, 'Births')), 'deaths': k1(K(I, y, 'Deaths')), 'tfr max': f"{F(tmax,'TFR'):.2f} at its {tmax} peak", 'below 2.1': f"until {below}",
 'pass Kenya': str(pk), 'double': f"by {dbl}", 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)), 'net outflow': k1(-K(I, y, 'NetMigrations')),
 'natural': m(K(I, y, 'NatChange')), 'urban 1950': p1(U[1950]),
}
sys.exit(run('uganda', I, exp, ['population (millions)', 'density', 'pass Kenya'], yrs) > 0)
