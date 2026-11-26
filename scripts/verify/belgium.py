# Run after `npm run build`: python3 scripts/verify/belgium.py
# Independent check of every figure on /population/belgium/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'BEL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/belgium.json'))['tableYears']
E1 = countries(y, 1e6, EUROPE)
assert [k for k in E1 if all(K(k, yr, 'NetMigrations') > 0 for yr in R)] == [I]
it = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); il = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (it, il) == (2022, 1982)
nn = [yr for yr in R if K(I, yr, 'NatChange') < 0]; assert nn[:3] == [1975, 2020, 2022] and all(K(I, yr, 'NatChange') < 0 for yr in range(2022, 2101))
bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert bt == 1964
assert F(1971, 'TFR') >= 2.1 and all(F(yr, 'TFR') < 2.1 for yr in range(1972, y + 1)); tl = min(range(1950, y + 1), key=lambda yr: F(yr, 'TFR')); assert tl == 2023
assert sorted(E1, key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['NLD', I] and sorted(countries(y, 0, {'926'}), key=lambda k: -P(k, y))[:4] == ['DEU', 'FRA', 'NLD', I]
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2044 and all(K(I, yr, 'NatChange') + K(I, yr, 'NetMigrations') < 0 < K(I, yr, 'NetMigrations') for yr in range(2045, 2101))
assert sorted(E1, key=lambda k: -(urban(k).get(y) or 0)).index(I) == 3
exp = exp_base(I, y, U) | {
 'now': f"{c(K(I, y, 'Deaths'))} deaths, {c(K(I, y, 'Births'))} births and a migration surplus of {c(K(I, y, 'NetMigrations'))}, which nets out at {c(K(I, y, 'PopChange'))}", 'mig': f"smallest in {il} ({c(K(I, il, 'NetMigrations'))}) and largest in {it} ({c(K(I, it, 'NetMigrations'))})",
 'births': f"The {bt} birth count, {c(K(I, bt, 'Births'))}, remains the highest", 'tfr': f"reached its lowest, {F(tl, 'TFR'):.2f}, in {tl}", 'le': f"fell from {F(2019, 'LEx'):.1f} to {F(2020, 'LEx'):.1f} in 2020",
 'pk': f"That year's {m(P(I, pk))} is the medium variant's high; the line then slides toward {m(P(I, 2100))}", '1950': f"Belgium counted {m(P(I, 1950))}",
 'ld': f"the largest ({c(K(I, it, 'NetMigrations'))}) in {it}",
}
sys.exit(run('belgium', I, exp, ['population (millions)', 'ld'], yrs) > 0)
