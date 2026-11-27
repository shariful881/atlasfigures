# Run after `npm run build`: python3 scripts/verify/bahrain.py
# Independent check of every figure on /country/bahrain/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SVN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/slovenia.json'))['tableYears']
I = 'BHR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/bahrain.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); v1 = countries(y, 1e6)
assert sorted(v1, key=lambda k: -f(k, y, 'PopDensity'))[:3] == ['SGP', 'HKG', I]
assert sorted(v1, key=lambda k: -SR(k, y))[:4] == ['QAT', 'ARE', 'OMN', I] and 14 < P(I, y) / P(I, 1950) < 14.5
assert sorted(k for k in v1 if urban(k)[y] >= 99.95) == [I, 'HKG', 'KWT', 'SGP'] or sorted(k for k in v1 if urban(k)[y] >= 99.95) == ['BHR', 'HKG', 'KWT', 'SGP']
assert all(K(I, yr, 'Births') > K(I, yr, 'Deaths') for yr in R)
assert [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [2011, 2019, 2020] and all(NM(yr) < 0 for yr in (2011, 2019, 2020))
assert max(R, key=NM) == 2008 and min(R, key=NM) == 2019 and all(F(yr, 'TFR') < 2.1 for yr in range(2016, 2101)) and F(2015, 'TFR') >= 2.1
exp = exp_base(I, y, U) | {
 'a': f"compared with {c(P(I, 1950))} in 1950", 'in': f"peaking at {c(NM(2008))} in 2008", 'out': f"2019 was the biggest outflow, {c(-NM(2019))}",
 'sr': f"{SR(I, y):.1f} males per hundred females", 'tfr': f"The 1958 fertility rate of {F(1958, 'TFR'):.2f}",
 'fut': f"reaching {m(P(I, 2050))} by 2050 and then {m(P(I, 2100))} at century",
 'ld': f"{c(P(I, 1950))}, about a fourteenth of today",
}
sys.exit(run('bahrain', I, exp, ['population (millions)', 'ld'], yrs) > 0)
