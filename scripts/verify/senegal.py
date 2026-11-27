# Run after `npm run build`: python3 scripts/verify/senegal.py
# Independent check of every figure on /country/senegal/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'SEN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/senegal.json'))['tableYears']
ALL = countries(y); WAF = {'914'}; WB = countries(y, 1e7, WAF); AB = countries(y, 1e7, AFRICA)
assert sorted(WB, key=lambda k: -f(k, y, 'LEx'))[0] == I and sorted(WB, key=lambda k: f(k, y, 'IMR'))[0] == I
assert sorted(WB, key=lambda k: -(f(k, y, 'LEx') - f(k, 2000, 'LEx')))[:2] == ['NER', I]
assert sorted(AB, key=lambda k: f(k, y, 'IMR') / f(k, 2000, 'IMR')).index(I) == 3
assert [yr for yr in R if SR(I, yr) > 100] == list(range(1964, 1983)) + list(range(2016, 2048))
assert all(K(I, yr, 'NetMigrations') < 0 for yr in range(1975, 2013)) and all(K(I, yr, 'NetMigrations') > 0 for yr in range(2013, 2023)) and K(I, 1974, 'NetMigrations') > 0 and K(I, 2023, 'NetMigrations') < 0
out = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 2010
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101))
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (half, tmax, under) == (2020, 1980, 2094) and 0.49 < F(y, 'TFR') / F(tmax, 'TFR') < 0.52
assert sorted(WB, key=lambda k: f(k, y, 'TFR'))[:2] == ['GHA', I] and sorted(countries(y, 0, WAF), key=lambda k: -P(k, y)).index(I) == 6
exp = exp_base(I, y, U) | {
 'le': f"Life expectancy was {F(1950, 'LEx'):.1f} in 1950, {F(2000, 'LEx'):.1f} in 2000 and is {F(y, 'LEx'):.1f} now", 'imr': f"went from {F(2000, 'IMR'):.1f} down to {F(y, 'IMR'):.1f}",
 'sr': f"{SR(I, y):.1f} males for each 100 females", 'out': f"most in {out}, near {k1(-K(I, out, 'NetMigrations'))}",
 'tfr': f"from a {tmax} high of {F(tmax, 'TFR'):.2f} to {F(y, 'TFR'):.2f} today", 'under': f"crosses 2.1 only in {under}", 'times': f"{P(I, y) / P(I, 1950):.1f} times its 1950 size",
 'pops': f"heads for {m(P(I, 2050))} in 2050 and is still rising in 2100, at {m(P(I, 2100))}", 'urb': f"Since {half} towns and cities", 'urb2': f"stands at {p1(U[y])}, compared with {p1(U[1950])} in 1950, and {p1(U[2050])} is projected for 2050",
 'mig now': f"about {k1(-K(I, y, 'NetMigrations'))} on balance",
 'ld': f"In 2000, {F(2000, 'IMR'):.1f} of every thousand babies died in their first year; now it is {F(y, 'IMR'):.1f}",
}
sys.exit(run('senegal', I, exp, ['population (millions)', 'ld'], yrs) > 0)
