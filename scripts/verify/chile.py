# Run after `npm run build`: python3 scripts/verify/chile.py
# Independent check of every figure on /country/chile/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'CHL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/chile.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); SAM = {'931'}
assert sorted(countries(y, 0, SAM), key=lambda k: f(k, y, 'TFR'))[0] == I and sorted(B, key=lambda k: f(k, y, 'TFR'))[:5] == ['KOR', 'TWN', 'UKR', 'CHN', I]
under = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert under == 1999 and all(F(yr, 'TFR') < 2.1 for yr in range(under, 2101))
pk = max(R, key=lambda yr: P(I, yr)); nn = next(yr for yr in R if K(I, yr, 'NatChange') < 0); bn = next(yr for yr in range(pk, 2101) if P(I, yr) < P(I, y))
assert (pk, nn, bn) == (2041, 2036, 2056) and all(K(I, yr, 'NatChange') < 0 for yr in range(nn, 2101)) and 0.32 < 1 - P(I, 2100) / P(I, y) < 0.34
assert [yr for yr in R if K(I, yr, 'NetMigrations') < 0] == list(range(1950, 1992)); it = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert it == 2018
assert sorted(countries(y, 0, SAM), key=lambda k: -f(k, y, 'LEx'))[0] == I
assert sorted(countries(y, 1e6, SAM), key=lambda k: -f(k, y, 'MedianAgePop'))[0] == I and sorted(countries(2050, 1e6, SAM), key=lambda k: -f(k, 2050, 'MedianAgePop'))[0] == I
bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert bt == 1991
exp = exp_base(I, y, U) | {
 'tfr': f"It was {F(1950, 'TFR'):.2f} in 1950, has been under 2.1 since {under} and has fallen by {F(2015, 'TFR') - F(y, 'TFR'):.2f} since 2015", 'births': f"greatest in {bt} (roughly {k1(K(I, bt, 'Births'))}); around {k1(K(I, y, 'Births'))}",
 'peak': f"Growth ends in {pk}, with {m(P(I, pk))} projected. Starting in {nn}", 'below': f"from {bn} the count", 'p2100': f"The 2100 projection, {m(P(I, 2100))}", 'ranks': f"from {ordn(rank(I, y))} to {ordn(rank(I, 2100))}",
 'mig': f"every year from 1950 to 1991", 'in': f"largest in {it}, about {k1(K(I, it, 'NetMigrations'))}, and are near {k1(K(I, y, 'NetMigrations'))} this year",
 'median': f"The median Chilean is {F(y, 'MedianAgePop'):.1f}, compared with {F(1990, 'MedianAgePop'):.1f} in 1990, and {F(2050, 'MedianAgePop'):.1f} is expected", 'le': f"longest life expectancy, {F(y, 'LEx'):.1f}", 'le 1950': f"up from {F(1950, 'LEx'):.1f} in 1950",
 'ld': f"{pk} is the projected high, {m(P(I, pk))}; natural decrease begins in {nn}",
}
sys.exit(run('chile', I, exp, ['population (millions)', 'ld'], yrs) > 0)
