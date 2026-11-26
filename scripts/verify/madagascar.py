# Run after `npm run build`: python3 scripts/verify/madagascar.py
# Independent check of every figure on /population/madagascar/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'MDG'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/madagascar.json'))['tableYears']
assert sorted(countries(y, 0, {'910'}), key=lambda k: -P(k, y)).index(I) == 5
mm = max(abs(K(I, yr, 'NetMigrations')) for yr in R); assert 18000 < mm < 19000
imr = [F(yr, 'IMR') for yr in range(2015, 2024)]; assert max(imr) - min(imr) < 0.5 and F(2010, 'IMR') - F(2015, 'IMR') > 2.5
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (tmax, under) == (1953, 2096) and all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101)) and U[2050] < 50
exp = exp_base(I, y, U) | {
 'mig max': f"about {k1(mm)}", 'births': f"roughly {m(K(I, y, 'Births'))} babies", 'deaths': f"some {k1(K(I, y, 'Deaths'))} deaths", 'nat': f"near {k1(K(I, y, 'NatChange'))}",
 'mig': f"come to about {k1(-K(I, y, 'NetMigrations'))}", 'times': f"some {P(I, y) / P(I, 1950):.1f} times the {m(P(I, 1950))}",
 'imr': f"fell from {F(2000, 'IMR'):.1f} deaths per 1,000 live births in 2000 to {F(2015, 'IMR'):.1f} in 2015", 'imr 2023': f"when it was {F(2023, 'IMR'):.1f}",
 'imr now': f"to {F(y, 'IMR'):.1f} in 2026", 'imr 2030': f"reaches {F(2030, 'IMR'):.1f} by 2030",
 'tfr max': f"{F(tmax, 'TFR'):.2f} per woman, belongs to {tmax}", 'under': f"until {under}",
 'pop 2100': f"Close to {m(P(I, 2100))}", 'pop 2050': f"with {m(P(I, 2050))} reached", 'ranks': f"from {ordn(rank(I, y))} place now to {ordn(rank(I, 2100))}",
 'urban 2050': f"and {p1(U[2050])} in 2050", 'ld': f"closes with {m(P(I, 2100))}",
}
sys.exit(run('madagascar', I, exp, ['population (millions)', 'ld'], yrs) > 0)
