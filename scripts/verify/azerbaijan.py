# Run after `npm run build`: python3 scripts/verify/azerbaijan.py
# Independent check of every figure on /population/azerbaijan/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'AZE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/azerbaijan.json'))['tableYears']
assert 3.2 < P(I, y) / P(I, 1950) < 3.4 and F(y, 'PopGrowthRate') < 0.5 * F(1990, 'PopGrowthRate')
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1989, 1996)
tm = max(R, key=lambda yr: F(yr, 'TFR')); r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert (tm, r21, bt) == (1962, 1996, 1988)
sl = min(range(1980, y + 1), key=lambda yr: SR(I, yr)); assert sl == 1999
pk = max(R, key=lambda yr: P(I, yr)); nn = next(yr for yr in R if K(I, yr, 'NatChange') < 0); assert (pk, nn) == (2050, 2049)
assert next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1968 and abs(U[2050] - U[y]) < 1
W1 = countries(y, 1e6, {'922'}); assert sorted(W1, key=lambda k: -f(k, y, 'IMR')).index(I) == 3 and sorted(countries(y, 0, {'922'}), key=lambda k: -P(k, y)).index(I) == 7
exp = exp_base(I, y, U) | {
 'tfr': f"{F(tm, 'TFR'):.2f} per woman at the 1962 high to {F(1990, 'TFR'):.2f} in 1990", 'b': f"The most births in a year, {c(K(I, bt, 'Births'))}, came in {bt}; the {y} projection is {c(K(I, y, 'Births'))}",
 'mig': f"Net emigration was {c(-K(I, 1988, 'NetMigrations'))} in 1988 and {c(-K(I, out, 'NetMigrations'))} in 1989", 'in': f"net gain of {c(K(I, inn, 'NetMigrations'))}",
 'le': f"{F(1991, 'LEx'):.1f} in 1991 to {F(1992, 'LEx'):.1f} in 1992 and to {F(1994, 'LEx'):.1f} in 1994", 'sr': f"dipped to {SR(I, sl):.1f} in {sl} and have since recovered to {SR(I, y):.1f}", 'imr': f"At {F(y, 'IMR'):.1f} deaths",
 'pk': f"largest in {pk}, at {m(P(I, pk))}", 'p2100': f"declines to {m(P(I, 2100))} for 2100", 'urb': f"{p1(U[y])} today, {p1(U[2050])} in 2050", '1950': f"the UN counted {m(P(I, 1950))}",
 'ld': f"net departures were {c(-K(I, 1988, 'NetMigrations'))} in 1988",
}
sys.exit(run('azerbaijan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
