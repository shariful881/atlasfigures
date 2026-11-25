# Run after `npm run build`: python3 scripts/verify/sri-lanka.py
# Independent check of every figure on /population/sri-lanka/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y])}
I = 'LKA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
S = countries(y, 0, {'5501'})
assert sorted([k for k in S if urban(k).get(y) is not None], key=lambda k: urban(k)[y])[0] == I
big = [k for k in countries(y, 10e6) if urban(k).get(y) is not None]; assert sorted(big, key=lambda k: urban(k)[y]).index(I) == 3
assert all(14 < v < 23 for yr, v in U.items() if v is not None and yr <= 2050)
assert sorted(countries(y, 10e6), key=lambda k: -f(k, y, 'PopDensity')).index(I) == 10
assert sorted(S, key=lambda k: -f(k, y, 'LEx'))[:3] == ['MDV', 'IRN', I] and sorted(S, key=lambda k: -f(k, y, 'MedianAgePop')).index(I) < 4
assert all(F(yr, 'NetMigrations') < 0 for yr in range(2002, 2101)) and F(2001, 'NetMigrations') >= 0
otop = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births'))
below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101)) and max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')) == 1950
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nl = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0); assert all(K(I, yr, 'PopChange') < 0 for yr in range(peak + 1, 2101)) and peak - y == 25
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(K(I, y, 'PopChange') / 365),
 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE 2100': f"{F(2100,'LEx'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'net outflow': k1(-K(I, y, 'NetMigrations')), 'natural': k1(K(I, y, 'NatChange')), 'outflow record': f"{otop}, about {k1(-K(I, otop, 'NetMigrations'))}",
 'ratio 1950': f"{mf(I, 1950):.1f}", 'ratio': f"{mf(I):.1f}", 'tfr 1950': f"{F(1950,'TFR'):.2f}", 'below 2.1': f"since {below}", 'tfr': f"{F(y,'TFR'):.2f}",
 'births peak': f"{btop} at around {k1(K(I, btop, 'Births'))}", 'births': k1(K(I, y, 'Births')),
 'peak': f"{peak} at a population of {m(P(I, peak))}", 'natural loss': str(nl), 'pop 2100': m(P(I, 2100)),
}
sys.exit(run('sri-lanka', I, exp, ['population (millions)', 'urban', 'density'], yrs) > 0)
