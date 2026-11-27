# Run after `npm run build`: python3 scripts/verify/czechia.py
# Independent check of every figure on /country/czechia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'CZE'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/czechia.json'))['tableYears']
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert inn == 2022 and K(I, 2022, 'NetMigrations') > 3e5
assert sorted(countries(2022, 1e6, EUROPE), key=lambda k: -K(k, 2022, 'NetMigrations') / P(k, 2022))[0] == I and all(K(I, yr, 'NetMigrations') < 0 for yr in (2023, 2024, 2025))
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2023 and all(P(I, yr) < P(I, yr - 1) for yr in (2024, 2025, 2026))
bl = min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')); bt = max(R, key=lambda yr: K(I, yr, 'Births')); tl = min(range(1950, y + 1), key=lambda yr: F(yr, 'TFR')); assert (bl, bt, tl) == (y, 1974, 1999)
nn = [yr for yr in range(1950, y + 1) if K(I, yr, 'NatChange') < 0]; assert nn[0] == 1986 and len([v for v in nn if v >= 1994]) > (y - 1994 + 1) / 2 and all(K(I, yr, 'NatChange') < 0 for yr in range(y + 1, 2101))
assert sorted(countries(y, 0, {'923'}), key=lambda k: -P(k, y))[:5] == ['RUS', 'UKR', 'POL', 'ROU', I]
exp = exp_base(I, y, U) | {
 'in': f"net migration reached {c(K(I, 2022, 'NetMigrations'))} that year, against {c(K(I, 2021, 'NetMigrations'))} in 2021", 'out': f"{c(-K(I, 2023, 'NetMigrations'))}, {c(-K(I, 2024, 'NetMigrations'))} and {c(-K(I, 2025, 'NetMigrations'))}",
 'pk': f"After the 2023 maximum, {m(P(I, pk))}", 'p2100': f"down to {m(P(I, 2100))}", 'b': f"The {y} projection, {c(K(I, y, 'Births'))}, is below every annual figure since 1950; the high was {c(K(I, bt, 'Births'))} in {bt}",
 'tfr': f"in 1999, at {F(tl, 'TFR'):.2f}, recovered somewhat, and stands at {F(y, 'TFR'):.2f}", 'le': f"live {F(y, 'LEx'):.1f} years on average",
 'ld': f"{c(K(I, y, 'Deaths'))} deaths against {c(K(I, y, 'Births'))} births",
}
sys.exit(run('czechia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
