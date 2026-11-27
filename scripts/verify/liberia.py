# Run after `npm run build`: python3 scripts/verify/liberia.py
# Independent check of every figure on /country/liberia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'LBR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/liberia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert min(R, key=NM) == 1990 and -NM(1990) > 7e5 and max(R, key=NM) == 1997 and 0.27 < -NM(1990) / P(I, 1989) < 0.3
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1990, 1991, 1994] and min(R, key=lambda yr: F(yr, 'LEx')) == 1990
assert next(yr for yr in R if U.get(yr) and U[yr] > 50) == 1991 and max(R, key=lambda yr: P(I, yr)) == 2100 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2084 and 6.3 < P(I, y) / P(I, 1950) < 6.5
exp = exp_base(I, y, U) | {
 'out': f"The UN records {c(-NM(1990))} net departures that year", 'p89': f"the 1989 population ({m(P(I, 1989))})", 'le': f"at its lowest, {F(1990, 'LEx'):.1f} years", 'p91': f"reaching {m(P(I, 1991))}",
 'box94': f"{c(-NM(1994))}", 'in': f"1997 brought the most of any year ({c(NM(1997))}), with {c(NM(1998))} more in 1998", 'p97': f"back to {m(P(I, 1997))}", 'now': f"with {c(-NM(y))} net departures",
 'fut': f"reach {m(P(I, 2050))} around mid-century, then {m(P(I, 2100))} at its close", 'imr': f"{F(y, 'IMR'):.1f} per 1,000 births",
 'ld': f"{c(-NM(1990))} more departed than arrived",
}
sys.exit(run('liberia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
