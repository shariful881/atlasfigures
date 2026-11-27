# Run after `npm run build`: python3 scripts/verify/tajikistan.py
# Independent check of every figure on /country/tajikistan/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'TJK'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/tajikistan.json'))['tableYears']
CA = countries(y, 0, {'5500'}); B = countries(y, 1e7)
ut = max(range(1950, y + 1), key=lambda yr: U[yr]); assert ut == 1970 and U[y] < U[ut] - 10 and U[2050] < U[y] and all(v < 50 for v in U.values()) and 24 < U[y] < 28
assert sorted(B, key=lambda k: urban(k)[y]).index(I) == 6
lo = min(range(1980, y + 1), key=lambda yr: F(yr, 'LEx')); assert lo == 1993 and F(1993, 'LEx') < F(1991, 'LEx') - 6
fo = next(yr for yr in R if K(I, yr, 'NetMigrations') < 0); assert fo == 1979 and all(K(I, yr, 'NetMigrations') < 0 for yr in range(1989, 2101)); out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 1998
assert sorted(CA, key=lambda k: f(k, y, 'MedianAgePop'))[0] == I and sorted(CA, key=lambda k: -f(k, y, 'TFR'))[:2] == ['UZB', I] and sorted(CA, key=lambda k: -P(k, y))[:3] == ['UZB', 'KAZ', I]
tm = max(R, key=lambda yr: F(yr, 'TFR')); r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert (tm, r21, bt) == (1968, 2068, 2040)
assert max(R, key=lambda yr: P(I, yr)) == 2100 and 1.8 < P(I, 2100) / P(I, y) < 2 and SR(I, y) < 100
exp = exp_base(I, y, U) | {
 'urb': f"peaked at {p1(U[1970])} in 1970, slipped to {p1(U[1990])} in 1990 and stand at {p1(U[y])} now; the 2050 projection is {p1(U[2050])}",
 'le': f"slides from {F(1991, 'LEx'):.1f} in 1991 to {F(1993, 'LEx'):.1f} in 1993, and deaths go from {c(K(I, 1991, 'Deaths'))} to {c(K(I, 1993, 'Deaths'))}",
 'mig': f"they were {c(-K(I, 1992, 'NetMigrations'))} in 1992 and reached their largest, {c(-K(I, out, 'NetMigrations'))}, in {out}",
 'tfr': f"Women average {F(y, 'TFR'):.2f} children, second in the region to Uzbekistan, down from {F(tm, 'TFR'):.2f} in {tm}", 'births': f"Annual births, {c(K(I, y, 'Births'))} this year", 'sr': f"the sex ratio is {SR(I, y):.1f}",
 'fut': f"{m(P(I, 2100))}, still climbing, with {m(P(I, 2050))} passed",
 'ld': f"this year's is {c(-K(I, y, 'NetMigrations'))}",
}
sys.exit(run('tajikistan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
