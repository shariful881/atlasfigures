# Run after `npm run build`: python3 scripts/verify/south-africa.py
# Independent check of every figure on /population/south-africa/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
R = range(1950, 2101)
I = 'ZAF'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
sh = P(I, y) / sum(P(k, y) for k in countries(y, 0, {'913'})); assert 0.85 < sh < 0.9
assert sorted(countries(y, 0, AFRICA), key=lambda k: -f(k, y, 'NetMigrations'))[:2] == ['SDN', I]
assert F(2100, 'NetMigrations') > F(2100, 'NatChange') and all(F(yr, 'NetMigrations') > 0 for yr in range(2030, 2101))
assert all(P(I, yr + 1) > P(I, yr) for yr in range(1950, 2100))
lelow = min(range(1990, 2027), key=lambda yr: F(yr, 'LEx')); tmax = max(R, key=lambda yr: F(yr, 'TFR'))
below = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: F(yr, 'Births'))
assert 4.9 < P(I, y) / P(I, 1950) < 5.1
exp = exp_base(I, y, U) | {
 'net migration': k1(K(I, y, 'NetMigrations')), 'natural change': k1(K(I, y, 'NatChange')), 'nat 2100': k1(K(I, 2100, 'NatChange')),
 'LE 1990': f"{F(1990,'LEx'):.1f} years in 1990", 'LE low': f"{F(lelow,'LEx'):.1f} in {lelow}",
 'tfr max': f"{F(tmax,'TFR'):.2f} at the {tmax}", 'below 2.1': f"2.1 from {below}", 'births peak': f"{K(I,bt,'Births')/1e6:.1f} million in {bt}",
 'pop 2100': m(P(I, 2100)), 'pop 1950': m(P(I, 1950)), 'rank 2050': ordn(rank(I, 2050)) + ' in 2050', 'rank 2100': ordn(rank(I, 2100)) + ' in 2100',
}
sys.exit(run('south-africa', I, exp, ['population (millions)', 'tfr', 'net migration'], yrs) > 0)
