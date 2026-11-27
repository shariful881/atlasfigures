# Run after `npm run build`: python3 scripts/verify/uzbekistan.py
# Independent check of every figure on /country/uzbekistan/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101); EST = range(1950, 2024)
I = 'UZB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/uzbekistan.json'))['tableYears']
CA = {raw[I][y]['ParentID']}; ca = sorted(countries(y, 0, CA), key=lambda k: -P(k, y))
assert set(ca) == {'UZB', 'KAZ', 'TJK', 'KGZ', 'TKM'} and ca[:2] == [I, 'KAZ']
assert max(ca, key=lambda k: f(k, y, 'TFR')) == I
low = min(range(2000, 2024), key=lambda yr: F(yr, 'TFR')); high = max(range(low, 2024), key=lambda yr: F(yr, 'TFR'))
assert low == 2012 and high == 2023 and F(high, 'TFR') - F(low, 'TFR') > 1
assert max(EST, key=lambda yr: F(yr, 'Births')) == 2023
assert F(2030, 'MedianAgePop') < F(y, 'MedianAgePop') < F(2050, 'MedianAgePop')
assert all(P(I, yr) > P(I, yr - 1) for yr in range(2024, 2101))
below = next(yr for yr in range(2024, 2101) if F(yr, 'TFR') < 2.1); assert below == 2079
assert all(F(yr, 'NetMigrations') < 0 for yr in range(1990, 2101) if yr <= y) and 50 < U[y] < 52
exp = exp_base(I, y, U) | {
 'ratio': f"roughly {P(I, y) / P('KAZ', y):.1f} to one", 'tfr low': f"2012 low of {F(low, 'TFR'):.2f}", 'tfr high': f"reaching {F(high, 'TFR'):.2f} by 2023",
 'births peak': f"in 2023 at about {k1(K(I, 2023, 'Births'))}", 'times': f"about {P(I, y) / P(I, 1950):.1f}-fold", 'pop 1950': f"when it had {m(P(I, 1950))}",
 'mig': f"around {k1(-K(I, y, 'NetMigrations'))} for 2026", 'nat': f"the {k1(K(I, y, 'NatChange'))} surplus",
 'median 2000': f"from {F(2000, 'MedianAgePop'):.1f} in 2000", 'median 2030': f"to {F(2030, 'MedianAgePop'):.1f} by 2030", 'median 2050': f"to {F(2050, 'MedianAgePop'):.1f} in 2050",
 'pop 2050': f"goes to {m(P(I, 2050))} in 2050", 'pop 2100': f"on to {m(P(I, 2100))} in 2100", 'below': f"only in {below}",
 'ld 2050': f"Around {m(P(I, 2050))}",
}
sys.exit(run('uzbekistan', I, exp, ['population (millions)', 'ld 2050'], yrs) > 0)
