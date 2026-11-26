# Run after `npm run build`: python3 scripts/verify/burkina-faso.py
# Independent check of every figure on /population/burkina-faso/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'BFA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/burkina-faso.json'))['tableYears']
ALL = countries(y); WAF = {'914'}
drop = lambda k, a, b: f(k, a, 'TFR') - f(k, b, 'TFR')
assert max(ALL, key=lambda k: drop(k, 2015, 2020)) == I
assert max(countries(y, 1e7, WAF), key=lambda k: drop(k, 2000, y)) == I
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert (tmax, under) == (1981, 2080)
bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert bt == 2016 and all(K(I, yr, 'Births') < K(I, bt, 'Births') for yr in range(2017, y + 1))
mf = next(yr for yr in R if SR(I, yr) < 100); assert mf == 1967 and all(SR(I, yr) < 100 for yr in range(mf, y + 1))
pos = [yr for yr in range(1950, 2101) if K(I, yr, 'NetMigrations') >= 0]; assert min(pos) >= 2000 and max(pos) <= 2005
half = next(yr for yr in range(y, 2051) if U[yr] > 50); assert half == 2047
assert sorted(countries(y, 0, WAF), key=lambda k: -P(k, y)).index(I) == 5 and f(I, 2100, 'PopGrowthRate') < 0.1
exp = exp_base(I, y, U) | {
 'drop': f"slid from {F(2015, 'TFR'):.2f} to {F(2020, 'TFR'):.2f}", 'tfr max': f"against a high of {F(tmax, 'TFR'):.2f} in {tmax}",
 'births top': f"reached its high in {bt}, about {k1(K(I, bt, 'Births'))}", 'births now': f"{y} has about {k1(K(I, y, 'Births'))}",
 'sr 1950': f"ratio of {SR(I, 1950):.1f} men per 100 women", 'mf': f"each year from {mf}", 'sr now': f"the figure today is {SR(I, y):.1f}",
 'mig': f"this year's net loss is near {k1(-K(I, y, 'NetMigrations'))}", 'half': f"In {half}, on World Urbanization Prospects",
 'urban': f"{p1(U[1950])} of people were urban in 1950 against {p1(U[y])} today; the projection gives {p1(U[2050])} for 2050",
 'pop 2050': f"By 2050 it is {m(P(I, 2050))}", 'pop 2100': f"the last projected year, {m(P(I, 2100))}", 'under': f"below 2.1 in {under}", 'ld': f"was {F(2015, 'TFR'):.2f} for 2015 and {F(2020, 'TFR'):.2f} for 2020",
}
sys.exit(run('burkina-faso', I, exp, ['population (millions)', 'ld'], yrs) > 0)
