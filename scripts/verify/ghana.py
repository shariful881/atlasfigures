# Run after `npm run build`: python3 scripts/verify/ghana.py
# Independent check of every figure on /country/ghana/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'GHA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/ghana.json'))['tableYears']
WAF = {'914'}
assert sorted(countries(y, 0, WAF), key=lambda k: -P(k, y))[:2] == ['NGA', I]
assert sorted(countries(y, 1e7, WAF), key=lambda k: f(k, y, 'TFR'))[0] == I
assert sorted(countries(y, 1e7, WAF), key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['NGA', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); u4 = next(yr for yr in R if F(yr, 'TFR') < 4); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
uh = next(yr for yr in sorted(U) if U[yr] > 50); gmax = max(R, key=lambda yr: F(yr, 'PopGrowthRate'))
wf = next(yr for yr in R if SR(I, yr) < 100)
assert (tmax, u4, under, uh, gmax, wf) == (1969, 2015, 2079, 2009, 1959, 1969) and all(SR(I, yr) < 100 for yr in range(wf, 2101))
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101)) and F(y, 'TFR') < F(tmax, 'TFR') / 2
exp = exp_base(I, y, U) | {
 'tfr max': f"against {F(tmax, 'TFR'):.2f} at the {tmax} high", 'u4': f"below four since {u4}", 'under': f"2.1 only in {under}",
 'urban 1950': f"from {p1(U[1950])} in 1950", 'urban 2050': f"reaches {p1(U[2050])}", 'uh': f"In {uh}.", 'uh val': p1(U[uh]),
 'gmax': f"highest in {gmax}, at {p1(F(gmax, 'PopGrowthRate'))}", 'change': f"about {k1(K(I, y, 'PopChange'))} more people",
 'pop 2050': f"are {m(P(I, 2050))} for mid-century", 'pop 2100': f"{m(P(I, 2100))} for 2100", 'g2100': f"just {p1(F(2100, 'PopGrowthRate'))}",
 'sr 1950': f"about {SR(I, 1950):.1f} males", 'sr now': f"ratio is {SR(I, y):.1f}", 'wf': f"every year since {wf}",
 'ld': f"less than half the {F(tmax, 'TFR'):.2f} of {tmax}",
}
sys.exit(run('ghana', I, exp, ['population (millions)', 'ld'], yrs) > 0)
