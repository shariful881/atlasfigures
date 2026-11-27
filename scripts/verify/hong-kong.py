# Run after `npm run build`: python3 scripts/verify/hong-kong.py
# Independent check of every figure on /country/hong-kong/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'HKG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/hong-kong.json'))['tableYears']
big1 = countries(y, 1e6)
assert min(big1, key=lambda k: f(k, y, 'TFR')) == I and max(big1, key=lambda k: f(k, y, 'LEx')) == I and min(big1, key=lambda k: SR(k, y)) == I
assert min(big1, key=lambda k: P(k, 2100) / P(k, y)) == I and 0.27 < P(I, 2100) / P(I, y) < 0.29
assert sorted(big1, key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['SGP', I]
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2020 and all(P(I, yr) < P(I, yr - 1) for yr in range(2021, 2101))
assert all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2021, 2101))
assert min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y and max(R, key=lambda yr: K(I, yr, 'Births')) == 1965
tl = min(range(1950, y + 1), key=lambda yr: F(yr, 'TFR')); tt = max(R, key=lambda yr: F(yr, 'TFR')); assert (tl, tt) == (2022, 1962) and F(y, 'TFR') < 1
exp = exp_base(I, y, U) | {
 'tfr': f"{F(y, 'TFR'):.2f} now, the lowest of any place above a million people, and {F(tl, 'TFR'):.2f} at the 2022 trough", 'tt': f"In 1962 the figure was {F(tt, 'TFR'):.2f}",
 'b': f"This year's {c(K(I, y, 'Births'))} births are the smallest annual total since 1950; 1965 had {c(K(I, 1965, 'Births'))}",
 'pk': f"tops out at {m(P(I, pk))}", 'd': f"deaths ({c(K(I, y, 'Deaths'))} this year)", 'fut': f"leaves {m(P(I, 2050))} by 2050 and only {m(P(I, 2100))} by 2100",
 'sr': f"{SR(I, y):.1f} men to 100 women", 'ma': f"half are over {F(y, 'MedianAgePop'):.1f}",
 'ld': f"The UN data give a sex ratio of {SR(I, y):.1f} males per hundred females",
}
sys.exit(run('hong-kong', I, exp, ['population (millions)', 'ld'], yrs) > 0)
