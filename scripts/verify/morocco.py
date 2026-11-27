# Run after `npm run build`: python3 scripts/verify/morocco.py
# Independent check of every figure on /country/morocco/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
I = 'MAR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/morocco.json'))['tableYears']
assert [yr for yr in R if F(yr, 'NetMigrations') >= 0] == [1950, 1951, 1952]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1962 and F(2000, 'TFR') < F(1980, 'TFR') / 2
below = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert below == 2030 and all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101)) and F(y, 'TFR') > 2.1
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0); assert peak == 2058 and nd == 2067
assert sorted(countries(y, 5e6, AFRICA), key=lambda k: -f(k, y, 'LEx'))[:3] == ['TUN', 'DZA', I]
assert sorted(countries(y, 1e7, AFRICA), key=lambda k: -f(k, y, 'MedianAgePop'))[:2] == ['TUN', I]
assert sorted(countries(y, 0, {'912'}), key=lambda k: -P(k, y)).index(I) == 3
exp = exp_base(I, y, U) | {
 'tfr 1980': f"1980 rate of {F(1980, 'TFR'):.2f}", 'tfr 2000': f"became {F(2000, 'TFR'):.2f} by 2000", 'tfr max': f"{tmax} high of {F(tmax, 'TFR'):.2f}",
 'below': f"under that line from {below}", 'births': f"about {k1(K(I, y, 'Births'))} a year",
 'mig': f"outflow is about {k1(-K(I, y, 'NetMigrations'))}", 'nat': f"larger at about {k1(K(I, y, 'NatChange'))}",
 'median 1970': f"{F(1970, 'MedianAgePop'):.1f}", 'median 2050': f"{F(2050, 'MedianAgePop'):.1f}",
 'peak': f"tops out in {peak} with {m(P(I, peak))}", 'nd': f"births from {nd}", 'pop 2100': f"falls back to {m(P(I, 2100))}",
 'ld peak': f"{peak}, at {m(P(I, peak))}",
}
sys.exit(run('morocco', I, exp, ['population (millions)', 'ld peak'], yrs) > 0)
