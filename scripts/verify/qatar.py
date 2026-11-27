# Run after `npm run build`: python3 scripts/verify/qatar.py
# Independent check of every figure on /country/qatar/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'QAT'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/qatar.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); b1 = countries(y, 1e6)
assert sorted(countries(y, 0), key=lambda k: -SR(k, y))[:2] == [I, 'ARE'] and sorted(b1, key=lambda k: -P(k, y) / P(k, 1950))[:2] == ['ARE', I] and 130 < P(I, y) / P(I, 1950) < 132
assert max(R, key=NM) == 2007 and P(I, 2010) > 2 * P(I, 2004) and [yr for yr in R if NM(yr) < 0] == [2020] and P(I, 2020) > P(I, 2019)
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101)) and all(K(I, yr, 'Births') > K(I, yr, 'Deaths') for yr in R) and U[y] > 99
assert next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2011 and all(F(yr, 'TFR') < 2.1 for yr in range(2011, 2101)) and 2.2 < P(I, 2100) / P(I, y) < 2.4
exp = exp_base(I, y, U) | {
 'sr': f"{SR(I, y):.1f} males per hundred females", 'mf': f"Male residents total {m(f(I, y, 'TPopulationMale1July') * 1000)}, female ones {round(f(I, y, 'TPopulationFemale1July'))} thousand",
 'g': f"the 1950 estimate was {c(P(I, 1950))} residents", 'dbl': f"from {round(P(I, 2004) / 1000)} thousand (2004) to {m(P(I, 2010))} (2010)", 'in': f"Net arrivals peaked in 2007 at {c(NM(2007))}",
 'out': f"2020 shows {c(-NM(2020))} net departures", 'fut': f"The dashed line ends at {m(P(I, 2100))}",
 'ld': f"In 2007, with {c(NM(2007))} net arrivals",
}
sys.exit(run('qatar', I, exp, ['population (millions)', 'ld'], yrs) > 0)
