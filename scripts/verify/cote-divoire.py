# Run after `npm run build`: python3 scripts/verify/cote-divoire.py
# Independent check of every figure on /country/cote-divoire/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'CIV'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/cote-divoire.json'))['tableYears']
mult = sorted(countries(y, 1e7), key=lambda k: -P(k, y) / P(k, 1950))
assert mult[:4] == ['ARE', 'JOR', 'SAU', I] and [k for k in mult if k in countries(y, 1e7, AFRICA)][0] == I
assert sorted(countries(y, 0, {'914'}), key=lambda k: -P(k, y)).index(I) == 2
assert all(F(yr, 'NetMigrations') > 0 for yr in range(1950, 1999)) and all(F(yr, 'NetMigrations') < 0 for yr in range(1999, 2015))
imax = max(range(1950, 1999), key=lambda yr: F(yr, 'NetMigrations')); omin = min(R, key=lambda yr: F(yr, 'NetMigrations'))
assert (imax, omin) == (1996, 2013) and all(abs(K(I, yr, 'NetMigrations')) < 30000 for yr in range(2015, y + 1))
gmax = max(R, key=lambda yr: F(yr, 'PopGrowthRate')); tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert (gmax, tmax) == (1974, 1972)
assert sorted(countries(y, 1e7, AFRICA), key=lambda k: -SR(k, y))[:2] == ['DZA', I]
climbs = {k: rank(k, y) - rank(k, 2100) for k in countries(y, 1e7)}; assert climbs[I] == 27 == max(climbs.values())
assert all(F(yr, 'TFR') >= 2.1 for yr in R) and all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101))
exp = exp_base(I, y, U) | {
 'times': f"factor of {P(I, y) / P(I, 1950):.1f}", 'pop 1950': f"({m(P(I, 1950))})", 'tfr max': f"{F(tmax, 'TFR'):.2f} in {tmax}", 'gmax': f"{p1(F(gmax, 'PopGrowthRate'))}, came in {gmax}",
 'in': f"{imax} had the most, close to {k1(K(I, imax, 'NetMigrations'))}", 'out': f"as many as {k1(-K(I, omin, 'NetMigrations'))} in {omin}", 'mig now': f"about {k1(K(I, y, 'NetMigrations'))} in favour",
 'sr': f"sex ratio is {SR(I, y):.1f}", 'pop 2100': f"total is {m(P(I, 2100))}", 'pop 2050': f"passing {m(P(I, 2050))}", 'ranks': f"from {ordn(rank(I, y))} to {ordn(rank(I, 2100))}",
 'climb': f"a {rank(I, y) - rank(I, 2100)}-place jump", 'tfr 2100': f"still {F(2100, 'TFR'):.2f}", 'ld': f"today's is {m(P(I, y))}",
}
sys.exit(run('cote-divoire', I, exp, ['population (millions)', 'ld'], yrs) > 0)
