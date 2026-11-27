# Run after `npm run build`: python3 scripts/verify/botswana.py
# Independent check of every figure on /country/botswana/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
AF = {'910', '911', '912', '913', '914'}
I = 'BWA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/botswana.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); af = countries(y, 1e6, AF)
assert U[1950] < 3 and next(yr for yr in range(1950, 2051) if U[yr] > 50) == 1996 and sorted(af, key=lambda k: f(k, y, 'PopDensity'))[:3] == ['NAM', 'LBY', I]
assert min(range(1980, y + 1), key=lambda yr: F(yr, 'LEx')) == 2001 and F(1987, 'LEx') > 62
assert max(R, key=lambda yr: P(I, yr)) == 2088 and all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2089)) and all(P(I, yr) < P(I, yr - 1) for yr in range(2089, 2101))
assert all(NM(yr) < 0 for yr in range(1950, 1972)) and all(NM(yr) < 0 for yr in range(2011, 2101)) and NM(2010) > 0 and min(R, key=NM) == 1970 and max(R, key=NM) == 1978
assert max(R, key=lambda yr: K(I, yr, 'Births')) == 2022 and 6.2 < P(I, y) / P(I, 1950) < 6.4
exp = exp_base(I, y, U) | {
 'u': f"a mere {p1(U[1950])} of residents counted as urban in 1950", 'u2': f"reads {p1(U[y])} now and should be {p1(U[2050])} by 2050",
 'le': f"{F(1987, 'LEx'):.1f} years in 1987, {F(2001, 'LEx'):.1f} in 2001, then a rebound to {F(y, 'LEx'):.1f}",
 'pk': f"the projected summit at {m(P(I, 2088))}; by 2100 the line eases back to {m(P(I, 2100))}", 'g': f"some 6.3 times 1950's {c(P(I, 1950))}",
 'nm': f"(deepest in 1970, {c(-NM(1970))}), the largest inflow in 1978 ({c(NM(1978))})",
 'ld': f"the peak year 1978, {c(NM(1978))}",
}
sys.exit(run('botswana', I, exp, ['population (millions)', 'ld'], yrs) > 0)
