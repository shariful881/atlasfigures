# Run after `npm run build`: python3 scripts/verify/lebanon.py
# Independent check of every figure on /country/lebanon/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'LBN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/lebanon.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert max(R, key=NM) == 2013 and NM(2013) > 7e5 and all(NM(yr) > 1e5 for yr in (2012, 2013, 2014)) and all(NM(yr) < -2e5 for yr in range(2015, 2020)) and min(R, key=NM) == 2019
assert [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == [2016, 2017, 2018, 2019, 2020]
assert F(1976, 'LEx') < 40 and F(1977, 'LEx') > 55 and F(1982, 'LEx') < F(1981, 'LEx') - 10
assert sorted(countries(y, 1e6, {'922'}), key=lambda k: -f(k, y, 'PopDensity'))[:3] == ['BHR', 'PSE', I]
assert max(R, key=lambda yr: P(I, yr)) == 2080 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2032 and U[y] > 90
exp = exp_base(I, y, U) | {
 'in': f"{c(NM(2013))} more than left", 'side': f"flanked by {c(NM(2012))} (2012) and {c(NM(2014))} (2014)", 'tot': f"In 2011 the count stood at {m(P(I, 2011))}; four years on it was {m(P(I, 2015))}",
 'out': f"net departures reached {c(-NM(2015))}", 'o19': f"most of all 2019 ({c(-NM(2019))})", 'p20': f"ending at {m(P(I, 2020))}", 'now': f"the balance is {c(-NM(y))} out",
 'le': f"to {F(1976, 'LEx'):.1f} years in 1976 (from {F(1974, 'LEx'):.1f} two years before) and to {F(1982, 'LEx'):.1f} in 1982",
 'pk': f"reaching {m(P(I, 2080))}",
 'ld': f"{c(NM(2013))} by the UN's estimate",
}
sys.exit(run('lebanon', I, exp, ['population (millions)', 'ld'], yrs) > 0)
