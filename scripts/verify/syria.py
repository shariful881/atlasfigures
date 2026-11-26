# Run after `npm run build`: python3 scripts/verify/syria.py
# Independent check of every figure on /population/syria/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'SYR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/syria.json'))['tableYears']
hi = max(range(1950, 2016), key=lambda yr: P(I, yr)); low = min(range(hi + 1, y + 1), key=lambda yr: P(I, yr)); assert (hi, low) == (2011, 2016)
lost = P(I, hi) - P(I, low); assert 3.6e6 < lost < 3.8e6
omin = min(R, key=lambda yr: F(yr, 'NetMigrations')); assert omin == 2013 and min(countries(2013), key=lambda k: f(k, 2013, 'NetMigrations')) == I
assert all(F(yr, 'NetMigrations') < 0 for yr in range(2011, 2018)) and all(F(yr, 'NetMigrations') > 0 for yr in range(2018, y + 1))
assert sorted(countries(2023), key=lambda k: -f(k, 2023, 'NetMigrations'))[:2] == ['USA', I]
imax = max(range(2018, 2101), key=lambda yr: F(yr, 'NetMigrations')); passed = next(yr for yr in range(2012, 2101) if P(I, yr) > P(I, hi)); assert (imax, passed) == (2023, 2023)
assert F(2015, 'LEx') < F(2010, 'LEx') - 10 and sorted(countries(y, 1e7), key=lambda k: -f(k, y, 'PopGrowthRate')).index(I) == 3
assert sorted(countries(y, 0, {'922'}), key=lambda k: -P(k, y)).index(I) == 4
peak = max(R, key=lambda yr: P(I, yr)); nn = next(yr for yr in R if F(yr, 'NatChange') < 0); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (peak, nn, under) == (2086, 2087, 2047)
exp = exp_base(I, y, U) | {
 'hi': f"Mid-2011 saw {m(P(I, hi))}; mid-2016, {m(P(I, low))}", 'lost': f"By roughly {m(lost)}", 'omin': f"in 2013 at about {m(-K(I, omin, 'NetMigrations'))}",
 'le': f"from {F(2010, 'LEx'):.1f} years in 2010 to {F(2015, 'LEx'):.1f} in 2015", 'in': f"in {imax}, at about {k1(K(I, imax, 'NetMigrations'))}", 'mig': f"about {k1(K(I, y, 'NetMigrations'))} in 2026",
 'passed': f"level again in {passed}", 'nat': f"Around {k1(K(I, y, 'NatChange'))} more births", 'under': f"below 2.1 in {under}", 'pop 2050': f"to {m(P(I, 2050))} by 2050",
 'peak': f"crests in {peak} with {m(P(I, peak))}", 'nn': f"({nn})", 'ld': f"tops out in {peak} with {m(P(I, peak))}",
}
sys.exit(run('syria', I, exp, ['population (millions)', 'ld'], yrs) > 0)
