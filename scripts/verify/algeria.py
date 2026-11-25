# Run after `npm run build`: python3 scripts/verify/algeria.py
# Independent check of every figure on /population/algeria/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
R = range(1950, 2101)
I = 'DZA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
assert max(countries(y, 0, AFRICA), key=land) == I
tlow = min(range(1990, 2016), key=lambda yr: F(yr, 'TFR')); tmax = max(R, key=lambda yr: F(yr, 'TFR'))
reb = max(range(tlow, y + 1), key=lambda yr: F(yr, 'TFR')); assert reb == 2015 and F(reb, 'TFR') - F(tlow, 'TFR') > 0.5
bt = max(R, key=lambda yr: F(yr, 'Births'))
assert sorted([k for k in countries(y, 5e6, AFRICA)], key=lambda k: -f(k, y, 'LEx'))[:2] == ['TUN', I]
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0)
assert sorted(countries(y, 0, {'912'}), key=lambda k: -P(k, y))[:3] == ['EGY', 'SDN', I]
assert F(2010, 'TFR') > F(2000, 'TFR') and F(2020, 'TFR') > F(2000, 'TFR')
exp = exp_base(I, y, U) | {
 'tfr low': f"{F(tlow,'TFR'):.2f} in {tlow}", 'tfr max': f"{F(tmax,'TFR'):.2f} in {tmax}", 'rebound': f"{F(reb,'TFR'):.2f} by {reb}",
 'births peak': f"{K(I,bt,'Births')/1e6:.1f} million in {bt}", 'land (millions)': m(land(I)) + ' km²',
 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'LE 1950': f"{F(1950,'LEx'):.1f} in 1950",
 'peak (m)': m(P(I, peak)), 'tfr reb': f"{F(reb,'TFR'):.2f}", 'tfr lo': f"{F(tlow,'TFR'):.2f}",
 'peak': f"{peak}, when the projected total levels off at {m(P(I, peak))}", 'natural decrease': f"starts in {nd}",
}
sys.exit(run('algeria', I, exp, ['population (millions)', 'tfr', 'peak (m)', 'tfr reb', 'tfr lo'], yrs) > 0)
