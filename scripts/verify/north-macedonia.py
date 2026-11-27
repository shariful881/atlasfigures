# Run after `npm run build`: python3 scripts/verify/north-macedonia.py
# Independent check of every figure on /country/north-macedonia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovenia.json'))['tableYears']
I = 'MKD'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/north-macedonia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert max(R, key=lambda yr: P(I, yr)) == 2005 and all(P(I, yr) < P(I, yr - 1) for yr in list(range(1991, 1995)) + list(range(2006, 2101)))
assert all(NM(yr) < 0 for yr in range(1982, 2101)) and NM(1981) >= 0 and min(R, key=NM) == 1993
assert max(R, key=lambda yr: K(I, yr, 'Births')) == 1954 and min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y
assert all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2020, 2101)) and K(I, 2019, 'Deaths') <= K(I, 2019, 'Births')
assert all(F(yr, 'TFR') < 2.1 for yr in range(1996, 2101)) and F(1995, 'TFR') >= 2.1 and min(yr for yr in R if U.get(yr, 0) > 50) == 1974
assert 0.45 < P(I, 2100) / P(I, y) < 0.5
exp = exp_base(I, y, U) | {
 'pk': f"2005, with {m(P(I, 2005))}", 'end': f"which closes on {c(round(P(I, 2100) / 1e3))} thousand",
 'nm': f"The heaviest single year, 1993, lost {c(-NM(1993))}; the 2026 estimate is {c(-NM(y))}",
 'b': f"highest in 1954 ({c(K(I, 1954, 'Births'))}) and bottom out now, {c(K(I, y, 'Births'))}",
 'le': f"between 2019 ({F(2019, 'LEx'):.1f}) and 2021 ({F(2021, 'LEx'):.1f})", 'le22': f"2022 was back at {F(2022, 'LEx'):.1f}",
 'ld': f"Peak net loss: {c(-NM(1993))}, in 1993",
}
sys.exit(run('north-macedonia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
