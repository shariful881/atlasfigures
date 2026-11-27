# Run after `npm run build`: python3 scripts/verify/kosovo.py
# Independent check of every figure on /population/kosovo/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovenia.json'))['tableYears']
I = 'XKX'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/kosovo.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert max(R, key=lambda yr: P(I, yr)) == 1997 and min(R, key=NM) == 1998 and 0.13 < -NM(1998) / P(I, 1997) < 0.14
assert all(P(I, yr) < P(I, yr - 1) for yr in (1998, 1999, 2000)) and P(I, 2001) > P(I, 2000) and 0.75 < P(I, y) / P(I, 1997) < 0.77
assert min(yr for yr in R if U.get(yr, 0) > 50) == 2024 and max(R, key=lambda yr: K(I, yr, 'Births')) == 1988
assert min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y and K(I, y, 'Births') < K(I, 1988, 'Births') / 2
assert all(NM(yr) < 0 for yr in range(2021, 2101)) and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2046, 2101)) and K(I, 2045, 'Deaths') <= K(I, 2045, 'Births')
exp = exp_base(I, y, U) | {
 'pk': f"1997's {m(P(I, 1997))} is the highest UN value", 'nm98': f"net migration of minus {c(-NM(1998))} in 1998",
 'nm99': f"followed by {c(-NM(1999))} in 1999", 'p00': f"to {m(P(I, 2000))} in 2000", 'le': f"sank to {F(1999, 'LEx'):.1f} in 1999 after {F(1998, 'LEx'):.1f} in 1998",
 'b': f"maximum of {c(K(I, 1988, 'Births'))}; the 2026 estimate, {c(K(I, y, 'Births'))}", 'tfr': f"from {F(1950, 'TFR'):.2f} (1950)",
 'fut': f"for {m(P(I, 2100))} by 2100", 'ld': f"minus {c(-NM(1999))} (1999)",
}
sys.exit(run('kosovo', I, exp, ['population (millions)', 'ld'], yrs) > 0)
