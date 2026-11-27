# Run after `npm run build`: python3 scripts/verify/georgia.py
# Independent check of every figure on /country/georgia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'GEO'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/georgia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert max(R, key=lambda yr: P(I, yr)) == 1988 and [yr for yr in range(1951, 2021) if P(I, yr) < P(I, yr - 1)][:27] == list(range(1989, 2016)) and P(I, 2016) > P(I, 2015)
assert all(NM(yr) < 0 for yr in range(1989, 2016)) and min(R, key=NM) == 1993 and NM(2022) > 0 and P(I, y) / P(I, 1988) < 0.70
assert all(abs(P(I, yr) / P(I, 2015) - 1) < 0.01 for yr in range(2016, y + 1))
dr = sorted(countries(y, 1e6), key=lambda k: P(k, y) / max(P(k, yr) for yr in range(1950, y + 1))); assert dr[:3] == ['MDA', 'LVA', I], dr[:3]
assert next(yr for yr in R if K(I, yr, 'Deaths') > K(I, yr, 'Births')) == 2021 and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2021, 2101))
exp = exp_base(I, y, U) | {
 'pk': f"well short of 1988's {m(P(I, 1988))}", 'out': f"the gap widest in 1993 at {c(-NM(1993))}", 'nm22': f"2022 even added {c(NM(2022))} through net arrivals",
 'nat': f"{c(K(I, y, 'Deaths'))} deaths, {c(K(I, y, 'Births'))} births", 'sr': f"Georgia has {SR(I, y):.1f} males", 'fut': f"the UN expects {m(P(I, 2100))}",
 'ld': f"1993: {c(-NM(1993))} more people went than came",
}
sys.exit(run('georgia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
