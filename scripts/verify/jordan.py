# Run after `npm run build`: python3 scripts/verify/jordan.py
# Independent check of every figure on /population/jordan/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'JOR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/jordan.json'))['tableYears']
M1 = countries(y, 1e6)
assert P(I, 1950) < 5e5 and 26 < P(I, y) / P(I, 1950) < 27 and sorted(M1, key=lambda k: -P(k, y) / P(k, 1950))[:4] == ['ARE', 'QAT', 'KWT', I]
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (inn, out) == (2014, 2025)
assert sorted(countries(2014), key=lambda k: -K(k, 2014, 'NetMigrations'))[:3] == ['USA', 'TUR', I]
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [2025] and -K(I, 2025, 'NetMigrations') > K(I, 2025, 'NatChange')
bt = max(R, key=lambda yr: K(I, yr, 'Births')); tm = max(R, key=lambda yr: F(yr, 'TFR')); r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert (bt, tm, r21) == (2041, 1969, 2044)
assert sorted(M1, key=lambda k: -urban(k)[y]).index(I) == 8 and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1970 and max(R, key=lambda yr: P(I, yr)) == 2100
assert sorted(countries(y, 0, {'922'}), key=lambda k: -P(k, y)).index(I) == 5
exp = exp_base(I, y, U) | {
 'in': f"net inflows of {c(K(I, 1990, 'NetMigrations'))} in 1990, {c(K(I, 2006, 'NetMigrations'))} in 2006, and {c(K(I, 2013, 'NetMigrations'))}, {c(K(I, 2014, 'NetMigrations'))} and {c(K(I, 2015, 'NetMigrations'))}",
 'out': f"They reached {c(-K(I, 2024, 'NetMigrations'))} in 2024 and {c(-K(I, 2025, 'NetMigrations'))} in 2025", 'dip': f"ended {c(P(I, 2024) - P(I, 2025))} below 2024's",
 'tfr': f"{F(tm, 'TFR'):.2f} at the 1969 high, {F(y, 'TFR'):.2f} now and under 2.1 from {r21}", 'bd': f"{c(K(I, y, 'Deaths'))} expected this year against {c(K(I, y, 'Births'))} births",
 'fut': f"{m(P(I, 2050))} is the projection for 2050 and {m(P(I, 2100))} the one for 2100", '1950': f"In 1950 Jordan had {m(P(I, 1950))}",
 'ld': f"with a net gain of {c(K(I, inn, 'NetMigrations'))} people",
}
sys.exit(run('jordan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
