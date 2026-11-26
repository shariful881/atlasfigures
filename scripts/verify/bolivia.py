# Run after `npm run build`: python3 scripts/verify/bolivia.py
# Independent check of every figure on /population/bolivia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'BOL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/bolivia.json'))['tableYears']
ALL = countries(y); SAM = {'931'}; S1 = countries(y, 1e6, SAM)
assert min(ALL, key=lambda k: f(k, 2021, 'LEx') - f(k, 2019, 'LEx')) == I; lb = next(yr for yr in range(2022, 2101) if F(yr, 'LEx') > F(2019, 'LEx')); assert lb == 2023
assert all(K(I, yr, 'NetMigrations') < 0 for yr in R); out = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 1996
assert min(S1, key=lambda k: f(k, y, 'MedianAgePop')) == I and max(S1, key=lambda k: f(k, y, 'TFR')) == I and max(S1, key=lambda k: f(k, y, 'IMR')) == I and min(S1, key=lambda k: f(k, y, 'LEx')) == I and min(S1, key=lambda k: f(k, y, 'PopDensity')) == I
assert [yr for yr in R if SR(I, yr) > 100] == list(range(1994, 2032))
pk = max(R, key=lambda yr: P(I, yr)); half = next(yr for yr in R if U.get(yr) and U[yr] > 50); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (pk, half, under) == (2086, 1985, 2047) and sorted(countries(y, 0, SAM), key=lambda k: -P(k, y)).index(I) == 7
exp = exp_base(I, y, U) | {
 'tfr': f"fertility, {F(y, 'TFR'):.2f}, is the highest in that group and falls under 2.1 only in {under}", 'imr': f"Infant mortality, {F(y, 'IMR'):.1f} per 1,000", 'le': f"life expectancy, {F(y, 'LEx'):.1f}, the lowest",
 'drop': f"{F(2019, 'LEx'):.1f} years in 2019, {F(2020, 'LEx'):.1f} in 2020, {F(2021, 'LEx'):.1f} in 2021. By {lb}", 'out': f"in {out}, was about {k1(-K(I, out, 'NetMigrations'))}; this year it is roughly {k1(-K(I, y, 'NetMigrations'))}",
 'sr': f"today there are {SR(I, y):.1f} of them", 'peak': f"reaches {m(P(I, pk))} in {pk} and closes the century at {m(P(I, 2100))}", 'urb': f"mostly urban since {half}; the share is {p1(U[y])} today",
 'ld': f"UN estimates show {F(2019, 'LEx'):.1f} years in 2019 and {F(2021, 'LEx'):.1f} in 2021",
}
sys.exit(run('bolivia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
