# Run after `npm run build`: python3 scripts/verify/belarus.py
# Independent check of every figure on /population/belarus/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'BLR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/belarus.json'))['tableYears']
E1 = countries(y, 1e6, EUROPE)
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 1993 and [yr for yr in range(1994, 2101) if P(I, yr) >= P(I, yr - 1)] == [2013, 2014, 2015, 2016]
assert next(yr for yr in R if K(I, yr, 'NatChange') < 0) == 1993 and all(K(I, yr, 'NatChange') < 0 for yr in range(1993, 2101)) and 0.48 < P(I, 2100) / P(I, y) < 0.5 and 1.25e6 < P(I, pk) - P(I, y) < 1.35e6
assert sorted(countries(y, 1e6), key=lambda k: SR(k, y)).index(I) == 6 and min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y and max(R, key=lambda yr: K(I, yr, 'Births')) == 1960
assert sorted(E1, key=lambda k: f(k, y, 'TFR')).index(I) == 3 and next(yr for yr in range(1960, 2101) if F(yr, 'TFR') < 2.1) == 1976 and sorted(E1, key=lambda k: f(k, y, 'LEx'))[:3] == ['MDA', 'RUS', I]
exp = exp_base(I, y, U) | {
 'lost': f"By about {m(P(I, pk) - P(I, y))}", 'pk': f"down from {m(P(I, pk))} at the 1993 peak", 'b': f"To {c(K(I, y, 'Births'))} this year, the smallest number recorded from 1950 on, against {c(K(I, y, 'Deaths'))} deaths. The record, {c(K(I, 1960, 'Births'))}, dates from 1960",
 'tfr': f"is {F(y, 'TFR'):.2f}, fourth-lowest", 'sr': f"a sex ratio of {SR(I, y):.1f}", 'le': f"life expectancy, {F(y, 'LEx'):.1f}", 'fut': f"{m(P(I, 2050))}, then {m(P(I, 2100))}",
 'ld': f"1960 saw {c(K(I, 1960, 'Births'))}",
}
sys.exit(run('belarus', I, exp, ['population (millions)', 'ld'], yrs) > 0)
