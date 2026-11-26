# Run after `npm run build`: python3 scripts/verify/cameroon.py
# Independent check of every figure on /population/cameroon/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'CMR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/cameroon.json'))['tableYears']
MAF = {'911'}
assert sorted(countries(y, 0, MAF), key=lambda k: -P(k, y))[:3] == ['COD', 'AGO', I]
assert max(yr for yr in range(1950, y + 1) if F(yr, 'PopGrowthRate') < 2.4) == 1982
mb = next(yr for yr in R if K(I, yr, 'Births') > 1e6); uh = next(yr for yr in sorted(U) if U[yr] > 50)
murb = sorted([k for k in countries(y, 0, MAF) if k in [r[4] for r in _rows]], key=lambda k: -urban(k)[y])
assert (mb, uh) == (2027, 2008) and murb.index(I) == 5 and len(murb) == 9 and U[2050] - U[y] < 4
assert 1.9 < F(y, 'LEx') / F(1950, 'LEx') < 2
gh = next(yr for yr in range(y + 1, 2101) if P(I, yr) > P('GHA', yr)); under = next(yr for yr in R if F(yr, 'TFR') < 2.1); tmax = max(R, key=lambda yr: F(yr, 'TFR'))
assert (gh, under, tmax) == (2049, 2100, 1980) and (rank(I, 1950), rank(I, y), rank(I, 2100)) == (72, 51, 28)
exp = exp_base(I, y, U) | {
 'change': f"about {k1(K(I, y, 'PopChange'))} extra", 'times': f"roughly {P(I, y) / P(I, 1950):.1f} times 1950's {m(P(I, 1950))}", 'mb': f"in {mb} yearly births",
 'urban': f"from {p1(U[1950])} in 1950 to {p1(U[y])} now", 'urban 2050': f"only {p1(U[2050])} by 2050", 'uh': p1(U[uh]),
 'le': f"{F(1950, 'LEx'):.1f} years for 1950 and {F(y, 'LEx'):.1f}", 'imr': f"fell from {F(1950, 'IMR'):.1f} to {F(y, 'IMR'):.1f}", 'tfr max': f"peaked at {F(tmax, 'TFR'):.2f} in {tmax}",
 'gh': f"In {gh}, on the medium", 'pop 2050': f"reaches {m(P(I, 2050))}", 'pop 2100': f"and {m(P(I, 2100))} in the final", 'ranks': f"from {ordn(rank(I, y))} to {ordn(rank(I, 2100))} worldwide; in 1950 it ranked {ordn(rank(I, 1950))}",
 'ld': f"yes, in {gh}",
}
sys.exit(run('cameroon', I, exp, ['population (millions)', 'ld'], yrs) > 0)
