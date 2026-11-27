# Run after `npm run build`: python3 scripts/verify/bulgaria.py
# Independent check of every figure on /country/bulgaria/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'BGR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/bulgaria.json'))['tableYears']
big1 = countries(y, 1e6)
assert sorted(k for k in big1 if P(k, y) < P(k, 1950)) == [I, 'HRV', 'LVA'] and min(big1, key=lambda k: P(k, y) / P(k, 1950)) == I
def streak(k):
    n = 0
    for yr in range(y, 1950, -1):
        if P(k, yr) < P(k, yr - 1): n += 1
        else: break
    return n
assert max(range(1950, y + 1), key=lambda yr: P(I, yr)) == 1988 and streak(I) == 38 and sorted(big1, key=lambda k: -streak(k))[:2] == ['SRB', I]
NM = lambda yr: K(I, yr, 'NetMigrations'); assert all(-NM(yr) > 110000 for yr in range(1989, 1993)) and all(NM(yr) > 0 for yr in range(2020, 2025)) and NM(2019) < 0 and NM(2025) < 0
assert all(K(I, yr, 'Births') < K(I, yr, 'Deaths') for yr in range(1990, 2101)) and K(I, 1989, 'Births') > K(I, 1989, 'Deaths') and 1.7 < K(I, y, 'Deaths') / K(I, y, 'Births') < 1.8
assert sorted(countries(y, 1e6, EUROPE), key=lambda k: f(k, y, 'LEx')).index(I) == 4
exp = exp_base(I, y, U) | {
 'pk': f"The count rose to {m(P(I, 1988))} in 1988", 'mig': f"{c(-NM(1989))} in 1989 and {c(-NM(1992))} in 1992", 'in': f"largest in 2020 at {c(NM(2020))}",
 'nat': f"{c(K(I, y, 'Deaths'))} deaths, {c(K(I, y, 'Births'))} births", 'b50': f"in 1950 there were {c(K(I, 1950, 'Births'))} births", 'fut': f"At {m(P(I, 2100))}, about half of today's figure, after {m(P(I, 2050))}",
 '50': f"below the {m(P(I, 1950))} of 1950",
 'ld': f"with {c(-NM(1992))} in 1992 the highest",
}
sys.exit(run('bulgaria', I, exp, ['population (millions)', 'ld'], yrs) > 0)
