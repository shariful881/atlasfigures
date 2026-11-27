# Run after `npm run build`: python3 scripts/verify/puerto-rico.py
# Independent check of every figure on /country/puerto-rico/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'PRI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/puerto-rico.json'))['tableYears']
lac = countries(y, 1e6, {'915', '916', '931'}); big1 = countries(y, 1e6)
NM = lambda yr: K(I, yr, 'NetMigrations')
assert sorted(big1, key=lambda k: f(k, y, 'TFR'))[3] == I and set(sorted(big1, key=lambda k: f(k, y, 'TFR'))[:3]) == {'HKG', 'KOR', 'TWN'} and F(y, 'TFR') < 1
assert sorted(big1, key=lambda k: P(k, 2100) / P(k, y))[:2] == ['HKG', I] and 0.30 < P(I, 2100) / P(I, y) < 0.32
assert max(R, key=lambda yr: P(I, yr)) == 2001 and min(R, key=NM) == 2017 and NM(2023) > 0 and P(I, 2017) < P(I, 2016)
assert next(yr for yr in R if K(I, yr, 'Deaths') > K(I, yr, 'Births')) == 2014 and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2014, 2101))
assert min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == 2022 and max(lac, key=lambda k: f(k, y, 'MedianAgePop')) == I and max(lac, key=lambda k: f(k, y, 'LEx')) == I
exp = exp_base(I, y, U) | {
 'pk': f"under its 2001 maximum, {m(P(I, 2001))}", 'tfr': f"against {F(1950, 'TFR'):.2f} in 1950", 'b': f"Births bottomed out in 2022 ({c(K(I, 2022, 'Births'))}); 1950 had {c(K(I, 1950, 'Births'))}",
 'out': f"Its largest net outflow: {c(-NM(2017))}, after {c(-NM(2016))} in 2016. The July count slid to {m(P(I, 2017))}, having been {m(P(I, 2016))}",
 'n23': f"by {c(NM(2023))} in 2023", 'fut': f"2050, {m(P(I, 2050))}; 2100, {m(P(I, 2100))}, near 31% of today",
 'ld': f"2017, when {c(-NM(2017))} more left than came",
}
sys.exit(run('puerto-rico', I, exp, ['population (millions)', 'ld'], yrs) > 0)
