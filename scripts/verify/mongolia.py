# Run after `npm run build`: python3 scripts/verify/mongolia.py
# Independent check of every figure on /country/mongolia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'MNG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/mongolia.json'))['tableYears']
assert min(countries(y, 1e6), key=lambda k: f(k, y, 'PopDensity')) == I and next(yr for yr in range(1950, 2051) if U[yr] > 50) == 1977 and all(U[yr] > 50 for yr in range(1977, 2051))
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1966 and [yr for yr in range(1950, y + 1) if F(yr, 'TFR') < 2.1] == [2003, 2004, 2005] and F(2015, 'TFR') > 3
assert next(yr for yr in range(2006, 2101) if F(yr, 'TFR') < 2.1) == 2042 and max(countries(y, 0, {'906'}), key=lambda k: f(k, y, 'TFR')) == I
assert max(R, key=lambda yr: K(I, yr, 'Births')) == 2015 and all(P(I, yr) >= P(I, yr - 1) for yr in range(1951, 2101))
exp = exp_base(I, y, U) | {
 'tfr': f"The rate was {F(1966, 'TFR'):.2f} in 1966 and {F(2005, 'TFR'):.2f} in 2005", 'tfr15': f"climbing to {F(2015, 'TFR'):.2f} in 2015", 'b': f"The record year for births: 2015, {c(K(I, 2015, 'Births'))}",
 'urb': "a majority ever since 1977", 'fut': f"Mid-century brings {m(P(I, 2050))}; 2100 closes on {m(P(I, 2100))}",
 'ld': f"{F(2005, 'TFR'):.2f} in 2005, {F(2015, 'TFR'):.2f} by 2015, {F(y, 'TFR'):.2f} now",
}
sys.exit(run('mongolia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
