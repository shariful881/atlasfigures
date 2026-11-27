# Run after `npm run build`: python3 scripts/verify/austria.py
# Independent check of every figure on /country/austria/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'AUT'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/austria.json'))['tableYears']
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert inn == 2022 and K(I, 2015, 'NetMigrations') > 1e5 and [yr for yr in R if K(I, yr, 'NetMigrations') < 0][-1] == 1983
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2023 and all(P(I, yr) < P(I, yr - 1) for yr in (2024, 2025, 2026))
assert all(K(I, yr, 'NatChange') < 0 for yr in range(2022, 2101)) and next(yr for yr in R if K(I, yr, 'NatChange') < 0) == 1975
hi = [yr for yr in R if F(yr, 'TFR') >= 2.1]; assert hi == list(range(1954, 1972)) and max(R, key=lambda yr: K(I, yr, 'Births')) == 1963
assert sorted(countries(y, 0, {'926'}), key=lambda k: -P(k, y)).index(I) == 4 and 1.3 < P(I, y) / P(I, 1950) < 1.33 and 0 < K(I, y, 'NetMigrations') < -K(I, y, 'NatChange')
assert sum(K(I, yr, 'NetMigrations') for yr in range(1984, y + 1)) > 3 * sum(K(I, yr, 'NatChange') for yr in range(1984, y + 1))
exp = exp_base(I, y, U) | {
 'in': f"in 2022 ({c(K(I, 2022, 'NetMigrations'))}) and 2015 ({c(K(I, 2015, 'NetMigrations'))})", 'pk': f"The high point, {m(P(I, pk))}, falls in 2023",
 'bd': f"deaths, {c(K(I, y, 'Deaths'))} this year, now exceed births, {c(K(I, y, 'Births'))}, and this year's net arrivals of {c(K(I, y, 'NetMigrations'))}",
 'bt': f"1963, with {c(K(I, 1963, 'Births'))}", 'tfr': f"The rate is {F(y, 'TFR'):.2f} today", 'fut': f"{m(P(I, 2050))} expected by 2050 and {m(P(I, 2100))} by 2100",
 'ld': f"followed by {c(K(I, 2015, 'NetMigrations'))} in 2015",
}
sys.exit(run('austria', I, exp, ['population (millions)', 'ld'], yrs) > 0)
