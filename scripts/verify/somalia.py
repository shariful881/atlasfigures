# Run after `npm run build`: python3 scripts/verify/somalia.py
# Independent check of every figure on /population/somalia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'SOM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/somalia.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); EAF = {'910'}
assert sorted(B, key=lambda k: -f(k, y, 'PopGrowthRate'))[0] == I and sorted(ALL, key=lambda k: -f(k, y, 'PopGrowthRate'))[:2] == ['CAF', I]
assert sorted(B, key=lambda k: f(k, y, 'MedianAgePop'))[0] == I
top = lambda yr: max(countries(yr), key=lambda k: f(k, yr, 'TFR')); assert [yr for yr in range(2015, y + 1) if top(yr) == I] == list(range(2019, 2024))
assert sorted(ALL, key=lambda k: -f(k, y, 'TFR'))[:2] == ['TCD', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1997 and all(F(yr, 'TFR') > 2.1 for yr in R)
assert min(R, key=lambda yr: F(yr, 'LEx')) == 1992 and F(1991, 'LEx') < 26 and F(2011, 'LEx') < 33
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1989, 1990, 1991, 1992]; back = next(yr for yr in range(1989, 2101) if P(I, yr) > P(I, 1988)); assert back == 1995
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1991, 1979)
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 2018 and sorted(countries(y, 1e7, EAF), key=lambda k: -urban(k)[y])[0] == I
dbl = next(yr for yr in R if P(I, yr) > 2 * P(I, y)); assert dbl == 2055
assert sorted(countries(y, 0, EAF), key=lambda k: -P(k, y)).index(I) == 8 and sorted(countries(2100, 0, EAF), key=lambda k: -P(k, 2100)).index(I) == 6
exp = exp_base(I, y, U) | {
 'births': f"About {k1(K(I, y, 'Births'))} births and {k1(K(I, y, 'Deaths'))} deaths", 'times': f"{P(I, y) / P(I, 1950):.1f} times its 1950 size", 'dbl': f"doubles again by {dbl}", 'p2100': f"seventh by 2100, at {m(P(I, 2100))}",
 'tfr': f"from a peak of {F(tmax, 'TFR'):.2f} in {tmax} to {F(y, 'TFR'):.2f} births per woman now", 'imr': f"Infant mortality is {F(y, 'IMR'):.1f} per 1,000 live births, down from {F(1950, 'IMR'):.1f} in 1950",
 'le': f"plunges from {F(1990, 'LEx'):.1f} in 1990 to {F(1991, 'LEx'):.1f} in 1991 and {F(1992, 'LEx'):.1f} in 1992, then returns to {F(1993, 'LEx'):.1f} in 1993; in 2011 it falls to {F(2011, 'LEx'):.1f}, having been {F(2010, 'LEx'):.1f} in 2010",
 'dip': f"from 1989 to 1992, to {m(P(I, 1992))}", 'out': f"peaked in {out} at about {k1(-K(I, out, 'NetMigrations'))}", 'in': f"{inn} brought the biggest surplus of arrivals, close to {k1(K(I, inn, 'NetMigrations'))}", 'le now': f"now stands at {F(y, 'LEx'):.1f}",
 'urb': f"dates from {half}: {p1(U[y])} today, against {p1(U[1950])} in 1950, with {p1(U[2050])} projected for 2050", 'back': f"the {m(P(I, 1988))} of 1988 was exceeded again in {back}", 'change': f"near {k1(K(I, y, 'PopChange'))} people",
 'ld': f"with {m(P(I, next(yr for yr in R if P(I, yr) > 2 * P(I, y))))}; growth continues to {m(P(I, 2100))} in 2100",
}
sys.exit(run('somalia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
