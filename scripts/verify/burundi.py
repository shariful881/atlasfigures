# Run after `npm run build`: python3 scripts/verify/burundi.py
# Independent check of every figure on /population/burundi/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'BDI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/burundi.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); BA = countries(y, 1e7, AFRICA)
assert sorted(BA, key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['RWA', I]
assert F(1972, 'LEx') < 27 and F(1971, 'LEx') > 43 and F(1993, 'LEx') < 38 and F(1992, 'LEx') > 44 and min(R, key=lambda yr: F(yr, 'LEx')) == 1972
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1972, 1973, 1993, 1997]
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1993, 1994)
assert sorted(B, key=lambda k: f(k, y, 'MedianAgePop')).index(I) == 6 and sorted(B, key=lambda k: -f(k, y, 'TFR')).index(I) == 6
assert U[y] > 3.2 * U[2000] and all(U[yr] <= 50 for yr in range(1950, 2051))
gain = lambda k: f(k, y, 'LEx') - f(k, 2000, 'LEx'); assert sorted(ALL, key=lambda k: -gain(k)).index(I) == 10
bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (bt, tmax, under) == (2015, 1989, 2095) and P(I, 2100) > P(I, 2099)
exp = exp_base(I, y, U) | {
 'urb': f"just {p1(U[y])} of the population", 'urb2': f"tripled from {p1(U[2000])} in 2000, and even by 2050 ({p1(U[2050])})",
 'le': f"falls from {F(1971, 'LEx'):.1f} in 1971 to {F(1972, 'LEx'):.1f} in 1972, its lowest, and from {F(1992, 'LEx'):.1f} in 1992 to {F(1993, 'LEx'):.1f} in 1993",
 'out': f"In {out} the net outflow was about {k1(-K(I, out, 'NetMigrations'))}", 'in': f"an inflow near {k1(K(I, inn, 'NetMigrations'))}",
 'median': f"{F(y, 'MedianAgePop'):.1f} years, the seventh-youngest", 'tfr': f"peaked at {F(tmax, 'TFR'):.2f} in {tmax} and the projection crosses 2.1 only in {under}", 'bt': f"greatest in {bt}",
 'gain': f"gained {gain(I):.1f} years and now stands at {F(y, 'LEx'):.1f}", 'p2100': f"which ends at {m(P(I, 2100))}",
 'ld': f"Minus {k1(-K(I, out, 'NetMigrations'))} or so",
}
sys.exit(run('burundi', I, exp, ['population (millions)', 'ld'], yrs) > 0)
