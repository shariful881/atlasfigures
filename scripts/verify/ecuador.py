# Run after `npm run build`: python3 scripts/verify/ecuador.py
# Independent check of every figure on /country/ecuador/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'ECU'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/ecuador.json'))['tableYears']
ALL = countries(y); SAM = {'931'}
assert sorted(countries(y, 0, SAM), key=lambda k: -f(k, y, 'PopDensity'))[:3] == [I, 'COL', 'VEN']
assert sorted(ALL, key=lambda k: f(k, 2020, 'LEx') - f(k, 2019, 'LEx'))[:2] == ['ARM', I]; lb = next(yr for yr in range(2021, 2101) if F(yr, 'LEx') > F(2019, 'LEx')); assert lb == 2023
assert [yr for yr in R if K(I, yr, 'NetMigrations') > 0] == [1950, 1951, 1983, 1984, 2014, 2015, 2016, 2017, 2018, 2019]
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); out = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert (inn, out) == (2018, 1997)
under = next(yr for yr in R if F(yr, 'TFR') < 2.1); tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert (under, tmax) == (2019, 1955) and all(F(yr, 'TFR') < 2.1 for yr in range(under, 2101))
pk = max(R, key=lambda yr: P(I, yr)); bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert (pk, bt) == (2063, 2011)
assert U[2025] - U[2010] < 1 and U[2050] - U[y] > 15 and sorted(countries(y, 0, SAM), key=lambda k: -P(k, y)).index(I) == 6
exp = exp_base(I, y, U) | {
 'dens': f"averages {round(F(y, 'PopDensity'))} people to the km² over {c(land(I))} km²", 'times': f"roughly {P(I, y) / P(I, 1950):.1f}-fold",
 'le': f"It dropped {F(2019, 'LEx') - F(2020, 'LEx'):.1f} years, from {F(2019, 'LEx'):.1f} to {F(2020, 'LEx'):.1f}", 'le21': f"It reached {F(2021, 'LEx'):.1f} in 2021, passed the 2019 mark again in {lb}",
 'in': f"the largest in {inn} at about {k1(K(I, inn, 'NetMigrations'))}; departures were heaviest in {out}, near {k1(-K(I, out, 'NetMigrations'))}", 'now': f"departures lead by around {k1(-K(I, y, 'NetMigrations'))}",
 'peak': f"{pk} is the projected top, with {m(P(I, pk))}; {m(P(I, 2100))} remain", 'tfr': f"highest in {tmax}, at {F(tmax, 'TFR'):.2f}, dropped under 2.1 in {under} and stands at {F(y, 'TFR'):.2f}", 'bt': f"most numerous in {bt}",
 'urb': f"climb from {p1(U[y])} to {p1(U[2050])} by 2050",
 'ld': f"from {F(2019, 'LEx'):.1f} years in 2019 to {F(2020, 'LEx'):.1f}, a fall exceeded only in Armenia",
}
sys.exit(run('ecuador', I, exp, ['population (millions)', 'ld'], yrs) > 0)
