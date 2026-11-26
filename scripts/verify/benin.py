# Run after `npm run build`: python3 scripts/verify/benin.py
# Independent check of every figure on /population/benin/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'BEN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/benin.json'))['tableYears']
B = countries(y, 1e7); WAF = {'914'}
assert all(F(yr, 'TFR') > 2.1 for yr in R); tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1981
assert [yr for yr in R if SR(I, yr) > 100] == list(range(2017, 2068)) and SR(I, 1950) < 88.5
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); rise = lambda k: (urban(k).get(2050) or 0) - (urban(k).get(y) or 0); assert half == 2021 and sorted(B, key=lambda k: -rise(k)).index(I) == 2
assert rank(I, y) - rank(I, 2100) == 22 and sorted(countries(y, 0, WAF), key=lambda k: -P(k, y)).index(I) == 8 and sorted(countries(2100, 0, WAF), key=lambda k: -P(k, 2100)).index(I) == 7
assert sorted(countries(y, 1e7, WAF), key=lambda k: -f(k, y, 'PopDensity'))[:3] == ['NGA', 'GHA', I]
inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (inn, out) == (1993, 1994)
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101)) and K(I, y, 'Births') > 3 * K(I, y, 'Deaths')
exp = exp_base(I, y, U) | {
 'tfr2100': f"it is {F(y, 'TFR'):.2f} births per woman today and {F(2100, 'TFR'):.2f} in 2100", 'tfr': f"eased to {F(y, 'TFR'):.2f} from {F(tmax, 'TFR'):.2f} in {tmax}",
 'births': f"about {k1(K(I, y, 'Births'))} to {k1(K(I, y, 'Deaths'))}", 'sr': f"The 1950 ratio was {SR(I, 1950):.1f} men to 100 women; males have outnumbered females since 2017, at {SR(I, y):.1f} per 100",
 'in': f"an inflow near {k1(K(I, inn, 'NetMigrations'))} in {inn}", 'out': f"net departures near {k1(-K(I, out, 'NetMigrations'))} in {out}",
 'urb': f"Just {p1(U[1950])} of Beninese were urban in 1950; since {half} they have been a majority, now {p1(U[y])}", 'u2050': f"{p1(U[2050])}, implies",
 'times': f"{P(I, y) / P(I, 1950):.1f}-fold", 'pops': f"rises past {m(P(I, 2050))} in 2050 toward {m(P(I, 2100))} in 2100, Benin climbs to {ordn(rank(I, 2100))}",
 'ld': f"the rate, {F(y, 'TFR'):.2f} now, is still {F(2100, 'TFR'):.2f} in 2100",
}
sys.exit(run('benin', I, exp, ['population (millions)', 'ld'], yrs) > 0)
