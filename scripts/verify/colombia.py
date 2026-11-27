# Run after `npm run build`: python3 scripts/verify/colombia.py
# Independent check of every figure on /country/colombia/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
R = range(1950, 2101)
I = 'COL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
assert all(F(yr, 'NetMigrations') < 0 for yr in range(1950, 2016)) and all(F(yr, 'NetMigrations') > 0 for yr in range(2016, y + 1))
inn = max(R, key=lambda yr: F(yr, 'NetMigrations')); assert abs(K(I, 2050, 'NetMigrations')) < 5000
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0)
tmax = max(R, key=lambda yr: F(yr, 'TFR')); below = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101))
bt = max(R, key=lambda yr: F(yr, 'Births'))
assert sorted(countries(y, 0, {'931'}), key=lambda k: -P(k, y))[:2] == ['BRA', I] and 4.3 < P(I, y) / P(I, 1950) < 4.7
exp = exp_base(I, y, U) | {
 'net 2010': f"-{round(-K(I,2010,'NetMigrations')/1000)}k", 'net record': f"+{round(K(I,inn,'NetMigrations')/1000)}k", 'net now': f"+{round(K(I,y,'NetMigrations')/1000)}k",
 'record year': f"{k1(K(I, inn, 'NetMigrations'))} in {inn}", 'net now (text)': k1(K(I, y, 'NetMigrations')),
 'peak': f"{m(P(I, peak))} in {peak}", 'natural decrease': f"starts in {nd}", 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
 'median 2050': f"{F(2050,'MedianAgePop'):.1f} by 2050", 'tfr max': f"{tmax} level of {F(tmax,'TFR'):.2f}", 'below 2.1': f"2.1 by {below}",
 'births peak': f"{bt} high of roughly {k1(K(I, bt, 'Births'))}", 'births now': k1(K(I, y, 'Births')),
 'urban 1950': p1(U[1950]), 'peak (m)': m(P(I, peak)), 'rec (k)': k1(K(I, inn, 'NetMigrations')), 'tfrmax': f"{F(tmax,'TFR'):.2f}", 'urban 2050': p1(U[2050]),
}
sys.exit(run('colombia', I, exp, ['population (millions)', 'tfr', 'growth', 'urban', 'urban 2050', 'peak (m)', 'rec (k)', 'tfrmax'], yrs) > 0)
