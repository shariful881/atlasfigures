# Run after `npm run build`: python3 scripts/verify/guinea.py
# Independent check of every figure on /country/guinea/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'GIN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/guinea.json'))['tableYears']
ALL = countries(y); WAF = {'914'}
assert sorted(ALL, key=lambda k: -f(k, y, 'IMR')).index(I) == 4 and sorted(ALL, key=lambda k: f(k, y, 'LEx')).index(I) == 7 and sorted(countries(y, 1e7, WAF), key=lambda k: -f(k, y, 'IMR'))[:2] == ['NGA', I]
assert [yr for yr in R if K(I, yr, 'NetMigrations') > 0] == [1990, 1991, 1993, 1995]
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (inn, out) == (1990, 2001)
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); half = next(yr for yr in R if U.get(yr) and U[yr] > 50)
assert (tmax, under, half) == (1987, 2088, 2043) and all(U[yr] >= U[yr - 1] for yr in range(1951, 2051))
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101)) and sorted(countries(y, 0, WAF), key=lambda k: -P(k, y)).index(I) == 7
exp = exp_base(I, y, U) | {
 'imr': f"At {F(y, 'IMR'):.1f} per 1,000 live births", 'imr90': f"though it was {F(1990, 'IMR'):.1f} in 1990", 'le': f"Life expectancy, {F(y, 'LEx'):.1f} years, is eighth-lowest in the world, up from {F(1950, 'LEx'):.1f} in 1950 and {F(2000, 'LEx'):.1f} in 2000",
 'in': f"largest in {inn} at about {k1(K(I, inn, 'NetMigrations'))}", 'out': f"about {k1(-K(I, out, 'NetMigrations'))}, in {out}", 'now': f"outflow of roughly {k1(-K(I, y, 'NetMigrations'))}",
 'times': f"the total is {P(I, y) / P(I, 1950):.1f} times", 'p2100': f"keeps rising to {m(P(I, 2100))} in 2100", 'tfr': f"topped out at {F(tmax, 'TFR'):.2f} in {tmax}; it is {F(y, 'TFR'):.2f} now and drops under 2.1 only in {under}",
 'urb': f"at {p1(U[y])} today it is projected to pass half in {half}", 'imr50': f"down from {F(1950, 'IMR'):.1f} in 1950",
 'ld': f"keeps climbing to {m(P(I, 2100))} by 2100",
}
sys.exit(run('guinea', I, exp, ['population (millions)', 'ld'], yrs) > 0)
