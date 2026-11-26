# Run after `npm run build`: python3 scripts/verify/peru.py
# Independent check of every figure on /population/peru/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'PER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/peru.json'))['tableYears']
assert sorted(countries(y, 0, {'931'}), key=lambda k: -P(k, y))[:4] == ['BRA', 'COL', 'ARG', I]
under = next(yr for yr in R if F(yr, 'TFR') < 2.1); tmax = max(R, key=lambda yr: F(yr, 'TFR'))
assert under == 2019 and all(F(yr, 'TFR') < 2.1 for yr in range(under, 2101)) and tmax == 1956 and F(tmax, 'TFR') > 6.9
assert all(F(yr, 'NetMigrations') < 0 for yr in range(1951, 2015)) and all(F(yr, 'NetMigrations') > 0 for yr in range(2015, 2028)) and all(F(yr, 'NetMigrations') < 0 for yr in range(2028, 2101))
omin = min(R, key=lambda yr: F(yr, 'NetMigrations')); imax = max(R, key=lambda yr: F(yr, 'NetMigrations')); assert (omin, imax) == (2007, 2018)
assert F(2021, 'LEx') < F(2020, 'LEx') < F(2019, 'LEx') < F(2022, 'LEx')
since = max(yr for yr in range(1950, 2021) if F(yr, 'LEx') < F(2021, 'LEx')); assert since == 2004
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0); assert (peak, nd) == (2066, 2067)
exp = exp_base(I, y, U) | {
 'out': f"heaviest in {omin} at about {k1(-K(I, omin, 'NetMigrations'))}", 'in': f"{imax} the biggest year at roughly {k1(K(I, imax, 'NetMigrations'))}", 'mig now': f"is about {k1(K(I, y, 'NetMigrations'))} in 2026",
 'le drop': f"By {F(2019, 'LEx') - F(2021, 'LEx'):.1f} years", 'le': f"from {F(2019, 'LEx'):.1f} years in 2019 to {F(2020, 'LEx'):.1f} in 2020 and {F(2021, 'LEx'):.1f} in 2021", 'since': f"since {since}",
 'le 2022': f"{F(2022, 'LEx'):.1f} in 2022", 'deaths': f"about {k1(K(I, 2021, 'Deaths'))}, compare with {k1(K(I, 2019, 'Deaths'))}",
 'tfr max': f"{F(tmax, 'TFR'):.2f} at its {tmax} high", 'med 1980': f"against {F(1980, 'MedianAgePop'):.1f} in 1980",
 'peak': f"high of {m(P(I, peak))}", 'nd': f"from {nd}", 'pop 2100': f"back to {m(P(I, 2100))}",
 'ranks': f"{ordn(rank(I, 2000))} in 2000, {ordn(rank(I, y))} today and {ordn(rank(I, 2100))} in 2100",
 'ld': f"{peak}, at {m(P(I, peak))} in the medium projection",
}
sys.exit(run('peru', I, exp, ['population (millions)', 'ld'], yrs) > 0)
