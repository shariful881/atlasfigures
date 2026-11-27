# Run after `npm run build`: python3 scripts/verify/argentina.py
# Independent check of every figure on /country/argentina/population/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
R = range(1950, 2101)
I = 'ARG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
LATAM = {'915', '916', '931'}
bt = max(R, key=lambda yr: F(yr, 'Births')); assert bt == 2014 and 0.3 < 1 - F(y, 'Births') / F(bt, 'Births') < 0.37
below = next(yr for yr in R if F(yr, 'TFR') < 2.1); tlow = min(range(1950, y + 1), key=lambda yr: F(yr, 'TFR'))
assert sorted(countries(y, 5e6, LATAM), key=lambda k: f(k, y, 'TFR')).index(I) == 3
assert max(countries(y, 10e6, LATAM), key=lambda k: urban(k)[y]) == I
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0); assert nd == peak
assert sorted(countries(y, 0, {'931'}), key=lambda k: -P(k, y))[:3] == ['BRA', 'COL', I] and 2.6 < P(I, y) / P(I, 1950) < 2.8
exp = exp_base(I, y, U) | {
 'births peak': f"{k1(K(I, bt, 'Births'))} in {bt}", 'births now': f"{k1(K(I, y, 'Births'))} in 2026", 'tfr 2015': f"{F(2015,'TFR'):.2f} in 2015",
 'below 2.1': f"2.1 in {below}", 'tfr low': f"{F(tlow,'TFR'):.2f} in {tlow}", 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]),
 'net now': f"{c(K(I, y, 'NetMigrations'))} people in 2026", 'net 1950': k1(K(I, 1950, 'NetMigrations')),
 'peak (m)': m(P(I, peak)), 'b14': k1(K(I, bt, 'Births')), 'b26': k1(K(I, y, 'Births')), 'tfr15': f"{F(2015,'TFR'):.2f}",
 'LE 1950': f"{F(1950,'LEx'):.1f} years", 'peak': f"{m(P(I, peak))} under", 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)),
}
sys.exit(run('argentina', I, exp, ['population (millions)', 'tfr', 'urban', 'pop 2100', 'peak (m)', 'b14', 'b26', 'tfr15', 'net 1950'], yrs) > 0)
