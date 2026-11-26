# Run after `npm run build`: python3 scripts/verify/oman.py
# Independent check of every figure on /population/oman/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'OMN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/oman.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert 12.2 < P(I, y) / P(I, 1950) < 12.6 and max(R, key=NM) == 2011 and NM(2011) > 4.9e5 and all(NM(yr) < 0 for yr in range(2018, 2022)) and NM(2022) > 3e5 and min(R, key=NM) == 2020
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [2019, 2020, 2021]
big1 = countries(y, 1e6); assert sorted(big1, key=lambda k: -SR(k, y))[:3] == ['QAT', 'ARE', I]
assert sorted(countries(y, 1e6, {'922'}), key=lambda k: f(k, y, 'PopDensity'))[:2] == ['SAU', I]
assert max(R, key=lambda yr: P(I, yr)) == 2100 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2037
exp = exp_base(I, y, U) | {
 'p50': f"starting from {c(P(I, 1950))} in 1950 and passing {m(P(I, 2000))} in 2000", 'in': f"net arrivals reached {c(NM(2011))}, then {c(NM(2012))} in 2012", 'out': f"largest in 2020 ({c(-NM(2020))})",
 'p21': f"down to {m(P(I, 2021))}", 'in22': f"{c(NM(2022))} net arrivals", 'sr': f"{SR(I, y):.1f} men per 100 women", 'fut': f"ending the series at {m(P(I, 2100))}",
 'ld': f"2011, with {c(NM(2011))}, followed by {c(NM(2012))} in 2012",
}
sys.exit(run('oman', I, exp, ['population (millions)', 'ld'], yrs) > 0)
