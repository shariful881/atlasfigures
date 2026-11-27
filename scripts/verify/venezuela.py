# Run after `npm run build`: python3 scripts/verify/venezuela.py
# Independent check of every figure on /country/venezuela/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'VEN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/venezuela.json'))['tableYears']
hi = max(range(1950, 2024), key=lambda yr: P(I, yr)); assert hi == 2016
assert [yr for yr in range(1950, 2031) if K(I, yr, 'PopChange') < 0] == [2017, 2018, 2019, 2020, 2021]
low = min(range(2017, y + 1), key=lambda yr: P(I, yr)); assert low == 2022
omin = min(R, key=lambda yr: F(yr, 'NetMigrations')); assert omin == 2018 and min(countries(2018), key=lambda k: f(k, 2018, 'NetMigrations')) == I
tot = sum(K(I, yr, 'NetMigrations') for yr in range(2015, y + 1)); assert -5e6 < tot < -4.8e6 and all(F(yr, 'NetMigrations') < 0 for yr in range(2010, y + 1))
back = next(yr for yr in range(2017, 2101) if P(I, yr) > P(I, hi)); peak = max(R, key=lambda yr: P(I, yr)); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (back, peak, under) == (2044, 2057, 2022) and all(F(yr, 'TFR') < 2.1 for yr in range(under, 2101))
assert sorted(countries(y, 0, {'931'}), key=lambda k: -P(k, y)).index(I) == 4 and (rank(I, 2010), rank(I, y), rank(I, 2100)) == (41, 54, 66)
exp = exp_base(I, y, U) | {
 'hi': m(P(I, hi)), 'omin': f"heaviest in {omin} at around {m(-K(I, omin, 'NetMigrations'))}", 'back': f"Not until {back}", 'tot': f"comes to about {m(-tot)}",
 'm2016': f"−{round(-K(I, 2016, 'NetMigrations') / 1000)}k", 'm2018': f"−{-K(I, omin, 'NetMigrations') / 1e6:.2f}M", 'mnow': f"−{round(-K(I, y, 'NetMigrations') / 1000)}k",
 'low': f"bottomed out at {m(P(I, low))}", 'nat': f"by some {k1(K(I, y, 'NatChange'))}", 'mig': f"takes roughly {k1(-K(I, y, 'NetMigrations'))}",
 'peak': f"high of {m(P(I, peak))} arrives in {peak}", 'age': f"was {F(2016, 'MedianAgePop'):.1f} in 2016 and is {F(y, 'MedianAgePop'):.1f}", 'births': f"from roughly {k1(K(I, 2016, 'Births'))} to {k1(K(I, y, 'Births'))}",
 'under': f"under 2.1 in {under}", 'ranks': f"{ordn(rank(I, y))} now, against {ordn(rank(I, 2010))} in 2010", 'pop 2100': f"population is {m(P(I, 2100))}",
 'ld': f"About {m(-tot)} on balance",
}
sys.exit(run('venezuela', I, exp, ['population (millions)', 'ld'], yrs) > 0)
