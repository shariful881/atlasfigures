# Run after `npm run build`: python3 scripts/verify/republic-of-the-congo.py
# Independent check of every figure on /country/republic-of-the-congo/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'COG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/republic-of-the-congo.json'))['tableYears']
assert F(1997, 'LEx') < F(1996, 'LEx') - 6 and F(1998, 'LEx') < F(1996, 'LEx')
NM = lambda yr: K(I, yr, 'NetMigrations'); assert max(R, key=NM) == 2009 and NM(2009) > 8e4 and all(NM(yr) < 0 for yr in range(2012, 2019))
assert next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1983 and sorted(countries(y, 1e6, {'911'}), key=lambda k: -urban(k)[y])[:4] == ['GAB', 'AGO', 'GNQ', I]
assert max(R, key=lambda yr: P(I, yr)) == 2100 and 2.9 < P(I, 2100) / P(I, y) < 3.1 and all(F(yr, 'TFR') > 2.1 for yr in R)
assert max(R, key=lambda yr: F(yr, 'TFR')) == 1972 and 7.8 < P(I, y) / P(I, 1950) < 8 and F(y, 'MedianAgePop') < 19
exp = exp_base(I, y, U) | {
 'u': f"The share was {p1(U[1950])} in 1950 and is {p1(U[y])} now", 'le': f"slid from {F(1996, 'LEx'):.1f} years (1996) to {F(1997, 'LEx'):.1f} (1997), recovering to {F(1998, 'LEx'):.1f} in 1998",
 'imr': f"from {F(1950, 'IMR'):.1f} in 1950 to {F(y, 'IMR'):.1f}", 'mig': f"{c(NM(2009))} more people arrived than left in 2009", 'out': f"with {c(-NM(2012))} net departures in 2012",
 'fut': f"{m(P(I, 2050))} for 2050, then {m(P(I, 2100))} for 2100", 'tfr': f"Fertility, {F(1972, 'TFR'):.2f} at its 1972 high and {F(y, 'TFR'):.2f} now",
 'ld': f"2009, with net arrivals of {c(NM(2009))}",
}
sys.exit(run('republic-of-the-congo', I, exp, ['population (millions)', 'ld'], yrs) > 0)
