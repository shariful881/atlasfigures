# Run after `npm run build`: python3 scripts/verify/uruguay.py
# Independent check of every figure on /country/uruguay/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'URY'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/uruguay.json'))['tableYears']
lac = countries(y, 1e6, {'915', '916', '931'})
assert max(lac, key=lambda k: urban(k)[y]) == I and max(lac, key=lambda k: urban(k)[1950]) == I
assert max(R, key=lambda yr: P(I, yr)) == 2020 and all(P(I, yr) < P(I, yr - 1) for yr in range(2021, 2101))
nat = [yr for yr in R if K(I, yr, 'Deaths') > K(I, yr, 'Births')]; assert nat[0] == 2021 and 2023 not in nat and all(yr in nat for yr in range(2024, 2101))
assert next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2004 and all(F(yr, 'TFR') < 2.1 for yr in range(2004, 2101)) and min(R, key=lambda yr: K(I, yr, 'NetMigrations')) == 2003
assert abs(P(I, 2100) / P(I, 1950) - 1) < 0.05
exp = exp_base(I, y, U) | {
 'u50': f"Back in 1950 its {p1(urban(I)[1950])} also led the region", 'pk': f"The 2020 count, {m(P(I, 2020))}, is the series maximum",
 'out': f"The deepest migration loss fell in 2003: {c(-K(I, 2003, 'NetMigrations'))} net", 'fut': f"{m(P(I, 2050))} for 2050; the closing 2100 figure, {m(P(I, 2100))}, nearly matches 1950's {m(P(I, 1950))}",
 'nat': f"{c(K(I, y, 'Deaths'))} deaths beside {c(K(I, y, 'Births'))} births",
 'ld': f"Uruguay, {p1(U[y])}; it was ahead in 1950 too, at {p1(urban(I)[1950])}",
}
sys.exit(run('uruguay', I, exp, ['population (millions)', 'ld'], yrs) > 0)
