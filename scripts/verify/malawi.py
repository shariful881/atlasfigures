# Run after `npm run build`: python3 scripts/verify/malawi.py
# Independent check of every figure on /population/malawi/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'MWI'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/malawi.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); BA = countries(y, 1e7, AFRICA); EAF = {'910'}
assert [yr for yr in range(1950, 2100) if K(I, yr, 'PopChange') < 0] == [1993, 1994] and [yr for yr in range(1951, 2101) if P(I, yr) < P(I, yr - 1)] == [1994, 1995]
assert all(K(I, yr, 'NetMigrations') > 0 for yr in range(1984, 1993)); it = max(range(1984, 1993), key=lambda yr: K(I, yr, 'NetMigrations')); assert it == 1987
gain = lambda k: f(k, y, 'LEx') - f(k, 2000, 'LEx'); assert max(ALL, key=gain) == I
lo = min(range(1986, y + 1), key=lambda yr: F(yr, 'LEx')); hi = max(range(1950, 1989), key=lambda yr: F(yr, 'LEx')); assert lo == 1989
ratio = lambda k: f(k, y, 'IMR') / f(k, 2000, 'IMR'); assert sorted(BA, key=ratio)[:2] == ['RWA', I]
assert sorted(BA, key=lambda k: -f(k, y, 'PopDensity')).index(I) == 4
assert sorted([k for k in B if k in [r[4] for r in _rows]], key=lambda k: urban(k)[y])[:2] == ['PNG', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert (tmax, under) == (1980, 2081)
assert sorted(countries(y, 0, EAF), key=lambda k: -P(k, y)).index(I) == 6
exp = exp_base(I, y, U) | {
 'gain': f"By {gain(I):.1f} years since 2000", 'le hi': f"After a high of {F(hi, 'LEx'):.1f} in {hi}", 'le': f"fell to {F(lo, 'LEx'):.1f} in {lo} and was still {F(2000, 'LEx'):.1f} in 2000; it is {F(y, 'LEx'):.1f} today",
 'imr': f"dropped from {F(2000, 'IMR'):.1f} to {F(y, 'IMR'):.1f} per 1,000", 'in': f"biggest in {it}, near {k1(K(I, it, 'NetMigrations'))}",
 'out': f"roughly {k1(-K(I, 1993, 'NetMigrations'))} (1993) and {k1(-K(I, 1994, 'NetMigrations'))} (1994)",
 'urban': f"urban share, {p1(U[y])}, is the second-smallest", 'urban 2050': f"projects {p1(U[2050])} for 2050",
 'pops': f"To {m(P(I, 2100))}, if the medium projection holds, up from {m(P(I, y))} now and {m(P(I, 2050))} in 2050",
 'tfr': f"Fertility, {F(y, 'TFR'):.2f} births per woman, has come down from {F(tmax, 'TFR'):.2f} in {tmax}", 'under': f"under 2.1 from {under}", 'dip': f"{m(P(I, 1993))} in 1993, is down to {m(P(I, 1995))} by 1995",
}
sys.exit(run('malawi', I, exp, ['population (millions)', 'density'], yrs) > 0)
