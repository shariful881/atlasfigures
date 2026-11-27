# Run after `npm run build`: python3 scripts/verify/slovenia.py
# Independent check of every figure on /country/slovenia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovenia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert max(R, key=lambda yr: P(I, yr)) == 2024 and all(P(I, yr) > P(I, yr - 1) for yr in range(1999, 2025)) and len(range(1999, 2025)) == 26 and all(P(I, yr) < P(I, yr - 1) for yr in range(2025, 2101))
assert all(P(I, yr) < P(I, yr - 1) for yr in range(1992, 1999)) and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2017, 2101)) and K(I, 2016, 'Deaths') <= K(I, 2016, 'Births')
assert max(R, key=lambda yr: K(I, yr, 'Births')) == 1953 and min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y and K(I, y, 'Births') < K(I, 1953, 'Births') / 2
assert sorted(countries(y, 1e6), key=lambda k: -f(k, y, 'MedianAgePop')).index(I) == 12 and min(range(1950, y + 1), key=lambda yr: F(yr, 'TFR')) == 2003
assert all(F(yr, 'TFR') < 2.1 for yr in range(1981, 2101)) and F(1980, 'TFR') >= 2.1 and max(R, key=NM) == 1986
exp = exp_base(I, y, U) | {
 'pk': f"The summit came in 2024 ({m(P(I, 2024))})", 'fut': f"{m(P(I, 2050))} as 2050 arrives; {m(P(I, 2100))} by century's end",
 'b': f"{c(K(I, 1953, 'Births'))} in 1953, the record, against {c(K(I, y, 'Births'))} expected in 2026", 'nm': f"1986 holding the biggest net gain, {c(NM(1986))}",
 'ld': f"versus {c(K(I, 1953, 'Births'))} in 1953",
}
sys.exit(run('slovenia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
