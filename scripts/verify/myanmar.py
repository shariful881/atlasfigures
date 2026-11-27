# Run after `npm run build`: python3 scripts/verify/myanmar.py
# Independent check of every figure on /country/myanmar/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
R = range(1950, 2101)
I = 'MMR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
below = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: F(yr, 'Births'))
assert all(F(yr, 'NetMigrations') < 0 for yr in range(1990, 2101))
out = min(R, key=lambda yr: F(yr, 'NetMigrations'))
SEA = countries(y, 0, {'920'}); assert min(SEA, key=lambda k: f(k, y, 'LEx')) == I
assert sorted(SEA, key=lambda k: urban(k)[y])[:2] == ['TLS', I]
assert sorted(SEA, key=lambda k: -P(k, y)).index(I) == 4
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0)
assert 2.9 < P(I, y) / P(I, 1950) < 3.2
exp = exp_base(I, y, U) | {
 'below 2.1': f"2.1 in {below}", 'tfr 1950': f"{F(1950,'TFR'):.2f} in 1950", 'births peak': f"{K(I,bt,'Births')/1e6:.1f} million, in {bt}", 'births now': k1(K(I, y, 'Births')),
 'net loss': k1(-K(I, y, 'NetMigrations')), 'natural change': k1(K(I, y, 'NatChange')), 'outflow max': f"about {k1(-K(I, out, 'NetMigrations'))}, was in {out}",
 'LE 1950': f"{F(1950,'LEx'):.1f} years", 'LE 2050': f"{F(2050,'LEx'):.1f}", 'peak': f"In {peak}, at about {m(P(I, peak))}", 'natural decrease': f"from {nd}",
 'pop 2100': m(P(I, 2100)), 'peak (m)': m(P(I, peak)), 'net (k)': k1(-K(I, y, 'NetMigrations')), 'out (k)': k1(-K(I, out, 'NetMigrations')), 'tfr50': f"{F(1950,'TFR'):.2f}", 'rank 2100': ordn(rank(I, 2100)), 'pop 1950': m(P(I, 1950)),
}
sys.exit(run('myanmar', I, exp, ['population (millions)', 'tfr', 'pop 2100', 'peak (m)', 'net (k)', 'out (k)', 'tfr50'], yrs) > 0)
