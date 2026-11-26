# Run after `npm run build`: python3 scripts/verify/panama.py
# Independent check of every figure on /population/panama/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'PAN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/panama.json'))['tableYears']
assert next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2025 and 99.9 < SR(I, y) < 100.1 and SR(I, 1950) > 104.5
assert sorted(countries(y, 1e6, {'916'}), key=lambda k: -f(k, y, 'LEx'))[:2] == ['CRI', I] and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1981
assert 5.3 < P(I, y) / P(I, 1950) < 5.5 and max(R, key=lambda yr: K(I, yr, 'Births')) == 2015 and max(R, key=lambda yr: P(I, yr)) == 2080 and max(R, key=lambda yr: F(yr, 'TFR')) == 1962
exp = exp_base(I, y, U) | {
 'tfr': f"{F(2024, 'TFR'):.2f} in 2024, {F(2025, 'TFR'):.2f} in 2025, {F(y, 'TFR'):.2f} now", 't62': f"The 1962 rate was {F(1962, 'TFR'):.2f}", 'b': f"topped out in 2015 with {c(K(I, 2015, 'Births'))}; {c(K(I, y, 'Births'))} are expected",
 'sr': f"the UN ratio is {SR(I, y):.1f} (men to 100 women) this year, down from {SR(I, 1950):.1f} in 1950", 'pk': f"{m(P(I, 2080))}, the medium-variant figure for 2080; by 2100 Panama is at {m(P(I, 2100))}",
 'ld': f"then {F(2025, 'TFR'):.2f} in 2025, the first sub-2.1 year",
}
sys.exit(run('panama', I, exp, ['population (millions)', 'ld'], yrs) > 0)
