# Run after `npm run build`: python3 scripts/verify/mozambique.py
# Independent check of every figure on /country/mozambique/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'MOZ'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/mozambique.json'))['tableYears']
assert [yr for yr in R if K(I, yr, 'PopChange') < 0] == [1987]
assert min(R, key=lambda yr: F(yr, 'NetMigrations')) == 1987 and max(R, key=lambda yr: F(yr, 'NetMigrations')) == 1994
assert all(F(yr, 'NetMigrations') < 0 for yr in range(1980, 1993)) and all(F(yr, 'NetMigrations') > 0 for yr in (1993, 1994, 1995))
assert sorted(countries(y, 1e7), key=lambda k: f(k, y, 'MedianAgePop')).index(I) == 5
EAF = {'910'}
assert sorted(countries(y, 0, EAF), key=lambda k: -P(k, y)).index(I) == 4
assert sorted(countries(y, 0, EAF), key=lambda k: -f(k, y, 'TFR'))[:3] == ['SOM', 'BDI', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); hund = next(yr for yr in R if P(I, yr) > 1e8)
uh = next(yr for yr in sorted(U) if U[yr] > 50)
assert (tmax, under, hund, uh) == (1972, 2087, 2091, 2044) and rank(I, y) == 44 and rank(I, 2100) == 21
exp = exp_base(I, y, U) | {
 'out 1987': f"reached roughly {k1(-K(I, 1987, 'NetMigrations'))}", 'fall 1987': f"slipped by {k1(-K(I, 1987, 'PopChange'))}",
 'in 1994': f"about {k1(K(I, 1994, 'NetMigrations'))} in 1994", 'tfr max': f"peaked at {F(tmax, 'TFR'):.2f} in {tmax}", 'under': f"until {under}",
 'hund': f"past 100 million in {hund}", 'pop 2050': f"brings {m(P(I, 2050))}", 'pop 2100': f"close, {m(P(I, 2100))}", 'ranks': f"from {ordn(rank(I, y))} to {ordn(rank(I, 2100))}",
 'urban': f"was {p1(U[1950])} in 1950", 'urban 2050': f"value is {p1(U[2050])}", 'uh': f"From {uh}", 'LE 1950': f"from {F(1950, 'LEx'):.1f} years",
 'ld 2100': f"with {m(P(I, 2100))} Mozambicans",
}
sys.exit(run('mozambique', I, exp, ['population (millions)', 'ld 2100'], yrs) > 0)
