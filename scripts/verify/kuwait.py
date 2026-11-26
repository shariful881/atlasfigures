# Run after `npm run build`: python3 scripts/verify/kuwait.py
# Independent check of every figure on /population/kuwait/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'KWT'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/kuwait.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); big1 = countries(y, 1e6)
assert min(R, key=NM) == 1990 and 0.53 < -NM(1990) / P(I, 1989) < 0.55 and max(R, key=NM) == 1991
assert min(big1, key=lambda k: min(K(k, yr, 'NetMigrations') / P(k, yr - 1) for yr in range(1951, y + 1))) == I
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1990, 1991, 1994, 2020, 2021] and NM(2022) > 3e5 and NM(2020) < 0
assert 32 < P(I, y) / P(I, 1950) < 34 and sorted(big1, key=lambda k: -P(k, y) / P(k, 1950))[:3] == ['ARE', 'QAT', I]
assert sorted(big1, key=lambda k: -SR(k, y)).index(I) == 4 and U[y] >= 99.95 and max(R, key=lambda yr: P(I, yr)) == 2100
exp = exp_base(I, y, U) | {
 'out': f"On balance {m(-NM(1990))}, about 54% of the {m(P(I, 1989))} counted for 1989", 'p90': f"{m(P(I, 1990))} in 1990, lower still in 1991 ({m(P(I, 1991))})", 'le': f"slid to {F(1990, 'LEx'):.1f} years",
 'in': f"{c(NM(1991))} net in 1991", 'back': f"passed its 1989 total again in {next(yr for yr in range(1992, 2101) if P(I, yr) > P(I, 1989))}", 'o20': f"({c(-NM(2020))} net leavers in 2020), then {c(NM(2022))} net newcomers",
 'fut': f"no peak appears before 2100 ({m(P(I, 2100))})",
 'ld': f"The 1991 net inflow, {c(NM(1991))}",
}
sys.exit(run('kuwait', I, exp, ['population (millions)', 'ld'], yrs) > 0)
