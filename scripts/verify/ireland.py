# Run after `npm run build`: python3 scripts/verify/ireland.py
# Independent check of every figure on /country/ireland/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'IRL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/ireland.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == list(range(1953, 1962)) + [1987, 1988, 1989]
assert next(yr for yr in range(1962, 2101) if P(I, yr) > P(I, 1950)) == 1968 and min(R, key=NM) == 1953 and max(R, key=NM) == 2006 and NM(2022) > 9e4
assert max(countries(y, 1e6, {'924'}), key=lambda k: P(k, y) / P(k, 2000)) == I and sorted(countries(y, 1e6, EUROPE), key=lambda k: -f(k, y, 'TFR')).index(I) == 4
assert next(yr for yr in R if K(I, yr, 'Births') < K(I, yr, 'Deaths')) == 2051 and max(R, key=lambda yr: P(I, yr)) == 2053 and max(R, key=lambda yr: K(I, yr, 'Births')) == 2009
exp = exp_base(I, y, U) | {
 'out': f"The 1953 net outflow alone was {c(-NM(1953))}", 'p61': f"reaching {m(P(I, 1961))}", 'o88': f"1988 alone saw {c(-NM(1988))}", 'p00': f"when the count was {m(P(I, 2000))}",
 'in': f"Net migration added {c(NM(2006))} in 2006 and {c(NM(2022))} in 2022", 'b': f"{c(K(I, 2009, 'Births'))}", 'pk': f"crests at {m(P(I, 2053))} (2053) and leaves {m(P(I, 2100))} for 2100",
 'ld': f"2006, at {c(NM(2006))} net",
}
sys.exit(run('ireland', I, exp, ['population (millions)', 'ld'], yrs) > 0)
