# Run after `npm run build`: python3 scripts/verify/slovakia.py
# Independent check of every figure on /country/slovakia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVK'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovakia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); nat = lambda yr: K(I, yr, 'Births') - K(I, yr, 'Deaths')
assert max(R, key=lambda yr: P(I, yr)) == 2023 and [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == [2001, 2002, 2003, 2004, 2021, 2024, 2025, 2026]
assert [yr for yr in range(1950, 2020) if nat(yr) < 0] == [2001, 2002, 2003] and all(nat(yr) < 0 for yr in range(2020, 2101))
assert max(R, key=NM) == 2022 and min(R, key=NM) == 2025 and F(2021, 'LEx') < F(2019, 'LEx') - 3
assert sorted(countries(y, 1e6, EUROPE), key=lambda k: urban(k)[y]).index(I) == 3 and 0.61 < P(I, 2100) / P(I, y) < 0.64 and next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1978
exp = exp_base(I, y, U) | {
 'pk': f"when it peaked at {m(P(I, 2023))}", 'fut': f"drops to {m(P(I, 2050))} by 2050 and to {m(P(I, 2100))} by 2100", 'nat': f"sets {c(K(I, y, 'Deaths'))} deaths against {c(K(I, y, 'Births'))} births",
 'le': f"dipped to {F(2021, 'LEx'):.1f} years in 2021 from {F(2019, 'LEx'):.1f} in 2019, then recovered to {F(2022, 'LEx'):.1f}",
 'mig': f"2022 brought {c(NM(2022))} net arrivals", 'out': f"2025 brought {c(-NM(2025))} net departures",
 'ld': f"The UN shows {c(NM(2022))} net arrivals in 2022",
}
sys.exit(run('slovakia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
