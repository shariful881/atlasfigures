# Run after `npm run build`: python3 scripts/verify/chad.py
# Independent check of every figure on /population/chad/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'TCD'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/chad.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); MAF = {'911'}
top = lambda yr: max(countries(yr), key=lambda k: f(k, yr, 'TFR'))
assert [yr for yr in range(2018, y + 1) if top(yr) == I] == [2024, 2025, 2026]
assert sorted(ALL, key=lambda k: f(k, y, 'LEx'))[:2] == ['NGA', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1993 and all(F(yr, 'TFR') > 2.1 for yr in R)
it = max(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert it == 2023 and K(I, 2024, 'NetMigrations') > 0 and K(I, 2025, 'NetMigrations') < 0 and K(I, y, 'NetMigrations') < 0
rise = lambda k: rank(k, y) - rank(k, 2100); assert rise(I) == 27 == rise('MLI') == max(rise(k) for k in B)
assert sorted(countries(y, 0, MAF), key=lambda k: -land(k))[:2] == ['COD', I] and sorted(countries(y, 0, MAF), key=lambda k: -P(k, y)).index(I) == 3
assert min(R, key=lambda yr: F(yr, 'MedianAgePop')) == 2002 and sorted(B, key=lambda k: f(k, y, 'MedianAgePop')).index(I) == 2
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 2049 and abs(U[2000] - U[2010]) < 0.5
assert 3.7 < K(I, y, 'Births') / K(I, y, 'Deaths') < 4
exp = exp_base(I, y, U) | {
 'tfr': f"Starting at {F(1950, 'TFR'):.2f} in 1950, fertility climbed to a high of {F(tmax, 'TFR'):.2f} in {tmax} and has eased to {F(y, 'TFR'):.2f}", 'tfr 2100': f"the projection, {F(2100, 'TFR'):.2f}, stays above 2.1",
 'births': f"about {k1(K(I, y, 'Births'))} births", 'deaths': f"the {k1(K(I, y, 'Deaths'))} deaths",
 'le': f"{F(y, 'LEx'):.1f} years at birth, against {F(1950, 'LEx'):.1f} in 1950 and {F(2000, 'LEx'):.1f} in 2000", 'imr': f"stand at {F(y, 'IMR'):.1f}, against {F(1950, 'IMR'):.1f} in 1950",
 'in': f"In {it} arrivals exceeded departures by some {k1(K(I, it, 'NetMigrations'))}", 'in 2024': f"by {k1(K(I, 2024, 'NetMigrations'))} in 2024", 'out': f"roughly {k1(-K(I, y, 'NetMigrations'))} more people leaving",
 'pops': f"{m(P(I, 2100))} by 2100, passing through {m(P(I, 2050))} in 2050", 'ranks': f"from {ordn(rank(I, y))} to {ordn(rank(I, 2100))} globally", 'times': f"{P(I, y) / P(I, 1950):.1f} times the 1950 figure",
 'urban': f"The urban share, {p1(U[y])}", 'half': f"majority only in {half}",
 'ld': f"led every country and area since 2024. The peak was {F(tmax, 'TFR'):.2f} in {tmax}",
}
sys.exit(run('chad', I, exp, ['population (millions)', 'ld'], yrs) > 0)
