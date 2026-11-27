# Run after `npm run build`: python3 scripts/verify/finland.py
# Independent check of every figure on /country/finland/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'FIN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/finland.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); B_ = lambda yr: K(I, yr, 'Births'); D_ = lambda yr: K(I, yr, 'Deaths')
assert max(R, key=lambda yr: P(I, yr)) == 2025 and all(P(I, yr) < P(I, yr - 1) for yr in range(2026, 2101))
assert [yr for yr in range(1951, 2026) if P(I, yr) < P(I, yr - 1)] == [1969, 1970]
assert next(yr for yr in R if B_(yr) < D_(yr)) == 2016 and all(B_(yr) < D_(yr) for yr in range(2016, 2101))
assert min(R, key=NM) == 1969 and max(R, key=NM) == 2022 and min(range(1950, y + 1), key=B_) == 2023
assert sorted(countries(y, 1e6, EUROPE), key=lambda k: f(k, y, 'TFR')).index(I) == 5 and 0.81 < P(I, 2100) / P(I, y) < 0.83
exp = exp_base(I, y, U) | {
 'pk': f"that year's projected count, {m(P(I, 2025))}", 'fut': f"By 2050 the count is {m(P(I, 2050))}; 2100 ends at {m(P(I, 2100))}",
 'nat': f"brings {c(D_(y))} deaths against {c(B_(y))} births", 'b': f"Births bottomed out at {c(B_(2023))} in 2023; 1950 had {c(B_(1950))}",
 'mig': f"In 1969 net departures reached {c(-NM(1969))}", 'in': f"hit {c(NM(2022))}, a series record; the 2026 figure is {c(NM(y))}",
 'ld': f"2023, with {c(B_(2023))}",
}
sys.exit(run('finland', I, exp, ['population (millions)', 'ld'], yrs) > 0)
