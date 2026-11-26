# Run after `npm run build`: python3 scripts/verify/moldova.py
# Independent check of every figure on /population/moldova/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
fromTop = lambda k: P(k, y) / max(P(k, yr) for yr in range(1950, y + 1))
I = 'MDA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/moldova.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); b1 = countries(y, 1e6)
assert max(R, key=lambda yr: P(I, yr)) == 1991 and sorted(b1, key=fromTop)[0] == I and 0.65 < fromTop(I) < 0.67 and sorted(b1, key=fromTop)[1:4] == ['LVA', 'GEO', 'BIH']
assert min(b1, key=lambda k: f(k, y, 'PopGrowthRate')) == I and sorted(b1, key=lambda k: SR(k, y))[:2] == ['HKG', I]
assert all(NM(yr) < 0 for yr in range(1979, 2022)) and len(range(1979, 2022)) == 43 and min(R, key=NM) == 2010 and max(R, key=NM) == 2022
assert [yr for yr in range(1992, 2101) if P(I, yr) > P(I, yr - 1)] == [2022, 2023] and all(U[yr] < 50 for yr in range(1950, 2051)) and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2018, 2101))
exp = exp_base(I, y, U) | {
 'pk': f"the UN count stood at {m(P(I, 1991))}", 'gr': f"fastest rate of decline among those nations, {p1(f(I, y, 'PopGrowthRate'))}",
 'out': f"the most in 2010 at {c(-NM(2010))}", 'in': f"The 2022 row then carries {c(NM(2022))} net arrivals", 'p23': f"(to {m(P(I, 2023))})",
 'sr': f"{SR(I, y):.1f} males per 100 females", 'nat': f"{c(K(I, y, 'Deaths'))} deaths expected in 2026 beside {c(K(I, y, 'Births'))} births", 'fut': f"the UN line reaches {m(P(I, 2100))}",
 'ld': f"the deepest year was 2010 ({c(-NM(2010))})",
}
sys.exit(run('moldova', I, exp, ['population (millions)', 'ld'], yrs) > 0)
