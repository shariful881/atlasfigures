# Run after `npm run build`: python3 scripts/verify/sierra-leone.py
# Independent check of every figure on /country/sierra-leone/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'SLE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/sierra-leone.json'))['tableYears']
assert sorted(countries(y), key=lambda k: -f(k, y, 'IMR'))[0] == I
assert all(K(I, yr, 'NetMigrations') < 0 for yr in range(1991, 2000)) and all(K(I, yr, 'NetMigrations') > 0 for yr in range(2000, 2004))
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1991, 2001)
osum = -sum(K(I, yr, 'NetMigrations') for yr in range(1991, 2000)); assert 9e5 < osum < 1e6
assert [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == [1992, 1993] and all(F(yr, 'LEx') < 45 for yr in range(1990, 2000))
pk = max(R, key=lambda yr: P(I, yr)); tm = max(R, key=lambda yr: F(yr, 'TFR')); r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert (pk, tm, r21, half) == (2092, 1987, 2071, 2032)
exp = exp_base(I, y, U) | {
 'imr': f"figure, {F(y, 'IMR'):.1f} deaths before age one", 'osum': f"close to {round(osum / 1e4) * 10} thousand altogether, most of all in 1991 ({c(-K(I, out, 'NetMigrations'))})", 'in': f"with {c(K(I, inn, 'NetMigrations'))} net arrivals in 2001",
 'le': f"from {F(1950, 'LEx'):.1f} years in 1950 and {F(2000, 'LEx'):.1f} in 2000 to {F(y, 'LEx'):.1f} now", 'tfr': f"The fertility peak came in {tm} ({F(tm, 'TFR'):.2f}); the rate now stands at {F(y, 'TFR'):.2f}",
 'pk': f"cresting at {m(P(I, pk))} in {pk}", 'urb': f"majority in {half}", '1995': f"{c(-K(I, 1995, 'NetMigrations'))}",
 'ld': f"peaking at {c(K(I, inn, 'NetMigrations'))} in 2001",
}
sys.exit(run('sierra-leone', I, exp, ['population (millions)', 'ld'], yrs) > 0)
