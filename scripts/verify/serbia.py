# Run after `npm run build`: python3 scripts/verify/serbia.py
# Independent check of every figure on /population/serbia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SRB'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/serbia.json'))['tableYears']
assert 'XKX' in raw and raw['XKX'][2026]['Location'].startswith('Kosovo (under UNSC res. 1244)')
def streak(k):
    n = 0
    for yr in range(y, 1950, -1):
        if P(k, yr) < P(k, yr - 1): n += 1
        else: break
    return n
big1 = countries(y, 1e6); assert streak(I) == 39 and max(big1, key=streak) == I and max(range(1950, y + 1), key=lambda yr: P(I, yr)) == 1987
assert all(K(I, yr, 'Births') < K(I, yr, 'Deaths') for yr in range(1992, 2101)) and K(I, 1991, 'Births') > K(I, 1991, 'Deaths')
assert F(1999, 'LEx') < F(1998, 'LEx') - 2 and F(2000, 'LEx') > F(1998, 'LEx')
NM = lambda yr: K(I, yr, 'NetMigrations'); assert all(NM(yr) < 0 for yr in range(2012, 2022)) and max(R, key=NM) == 2022 and NM(2022) > 4e4
assert SR(I, y) < 90.5 and 0.55 < P(I, 2100) / P(I, y) < 0.57
exp = exp_base(I, y, U) | {
 'pk': f"The top was {m(P(I, 1987))}, in 1987", 'nat': f"has {c(K(I, y, 'Deaths'))} deaths and {c(K(I, y, 'Births'))} births",
 'mig': f"with {c(-NM(2019))} in 2019 alone, then a swing in 2022 to a net inflow of {c(NM(2022))}", 'now': f"the balance is {c(-NM(y))} out",
 'le': f"to {F(1999, 'LEx'):.1f} years from {F(1998, 'LEx'):.1f} in 1998, and back at {F(2000, 'LEx'):.1f} in 2000", 'sr': f"who number {SR(I, y):.1f} per 100 women",
 'fut': f"{m(P(I, 2100))}, roughly 56% of the present count", 'f50': f"for 2050 it gives {m(P(I, 2050))}",
 'ld': f"Yes, {c(NM(2022))} net, the biggest inflow",
}
sys.exit(run('serbia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
