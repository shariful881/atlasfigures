# Run after `npm run build`: python3 scripts/verify/latvia.py
# Independent check of every figure on /country/latvia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovenia.json'))['tableYears']
I = 'LVA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/latvia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
pk = max(range(1950, y + 1), key=lambda yr: P(I, yr)); v1 = countries(y, 1e6)
fromTop = lambda k: P(k, y) / max(P(k, yr) for yr in range(1950, y + 1))
assert pk == 1989 and 0.68 < P(I, y) / P(I, pk) < 0.70 and sorted(v1, key=fromTop)[:2] == ['MDA', I]
assert sorted(v1, key=lambda k: P(k, y) / P(k, 1950))[:2] == ['BGR', I] and P(I, y) < P(I, 1950)
assert all(P(I, yr) < P(I, yr - 1) for yr in range(1990, 2023)) and len(range(1990, 2023)) == 33 and P(I, 2023) > P(I, 2022)
assert all(NM(yr) < 0 for yr in range(1989, 2022)) and NM(2022) > 0 and NM(2023) > 0 and min(R, key=NM) == 1992
assert all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(1992, 2101)) and K(I, 1991, 'Deaths') <= K(I, 1991, 'Births')
assert sorted(v1, key=lambda k: SR(k, y)).index(I) == 4
exp = exp_base(I, y, U) | {
 'a': f"fewer than the {m(P(I, 1950))} of 1950", 'pk': f"Residents climbed to {m(P(I, 1989))} in 1989",
 'nm': f"1992 was the heaviest, at {c(-NM(1992))}", 'dth': f"{c(K(I, y, 'Deaths'))} deaths set against {c(K(I, y, 'Births'))} births",
 'sr': f"a ratio of {SR(I, y):.1f} to 100", 'fut': f"{m(P(I, 2050))} come 2050, {c(round(P(I, 2100) / 1e3))} thousand by 2100",
 'ld': f"{m(P(I, y))} now, {m(P(I, 1950))} then",
}
sys.exit(run('latvia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
