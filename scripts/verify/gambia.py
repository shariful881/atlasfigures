# Run after `npm run build`: python3 scripts/verify/gambia.py
# Independent check of every figure on /population/gambia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
AF = {'910', '911', '912', '913', '914'}
I = 'GMB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/gambia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); af = countries(y, 1e6, AF)
assert sorted(af, key=lambda k: -f(k, y, 'PopDensity'))[:4] == ['MUS', 'RWA', 'BDI', I] and 9.3 < P(I, y) / P(I, 1950) < 9.5
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101)) and all(K(I, yr, 'Births') > K(I, yr, 'Deaths') for yr in R)
assert all(NM(yr) < 0 for yr in range(1994, 2101)) and NM(1993) > 0 and max(R, key=NM) == 1991 and next(yr for yr in range(1950, 2051) if U[yr] > 50) == 2003
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1976 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2065 and F(y, 'MedianAgePop') < 19
exp = exp_base(I, y, U) | {
 'g': f"The 1950 count of {c(P(I, 1950))} has multiplied roughly 9.4 times", 'nat': f"2026 expects {c(K(I, y, 'Births'))} births against {c(K(I, y, 'Deaths'))} deaths",
 'tfr': f"Fertility topped out in 1976 at {F(1976, 'TFR'):.2f} and is {F(y, 'TFR'):.2f} today", 'nm': f"({c(-NM(y))} net in 2026)", 'in': f"peaking at {c(NM(1991))} in 1991",
 'urb': f"{p1(U[1950])} in 1950, {p1(U[y])} today, {p1(U[2050])} projected for 2050", 'fut': f"Expect roughly {m(P(I, 2050))} as 2050 arrives, then {m(P(I, 2100))}",
 'ld': f"The busiest inflow year was 1991, with {c(NM(1991))}",
}
sys.exit(run('gambia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
