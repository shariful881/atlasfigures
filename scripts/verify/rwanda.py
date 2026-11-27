# Run after `npm run build`: python3 scripts/verify/rwanda.py
# Independent check of every figure on /country/rwanda/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'RWA'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/rwanda.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); BA = countries(y, 1e7, AFRICA); A1 = countries(y, 1e6, AFRICA)
assert P(I, 1994) < P(I, 1993) and P(I, 1995) < P(I, 1994) and P(I, 1996) > P(I, 1995); back = next(yr for yr in range(1996, 2101) if P(I, yr) > P(I, 1993)); assert back == 1998
assert min(R, key=lambda yr: F(yr, 'LEx')) == 1994 and max(R, key=lambda yr: F(yr, 'IMR')) == 1994
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (1994, 1996) and [yr for yr in range(1950, 2100) if K(I, yr, 'PopChange') < 0] == [1994]
gain = lambda k: f(k, y, 'LEx') - f(k, 2000, 'LEx'); assert sorted(ALL, key=lambda k: -gain(k))[:2] == ['MWI', I]
assert min(BA, key=lambda k: f(k, y, 'IMR') / f(k, 2000, 'IMR')) == I
top = lambda yr: max(countries(yr), key=lambda k: f(k, yr, 'TFR')); assert [yr for yr in range(1950, 1990) if top(yr) == I] == list(range(1950, 1968))
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1959
assert sorted(A1, key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['MUS', I] and sorted(B, key=lambda k: -f(k, y, 'PopDensity'))[:3] == ['BGD', 'TWN', I]
half = next(yr for yr in R if U.get(yr) and U[yr] > 50); assert half == 2045 and U[y] > 6 * U[1990]; sl = min(R, key=lambda yr: SR(I, yr)); assert sl == 2002
lost = P(I, 1993) - P(I, 1995); lp = lost / P(I, 1993) * 100; assert 28 < lp < 30 and P(I, y) > 2.5 * P(I, 1995)
exp = exp_base(I, y, U) | {
 'lost': f"shrank by {lost / 1e6:.1f} million, or {round(lp)}%, to {m(P(I, 1995))}", 'p1995': f"against {m(P(I, 1995))} for 1995", 'le': f"sinks from {F(1993, 'LEx'):.1f} (1993) to {F(1994, 'LEx'):.1f} (1994)",
 'imr': f"infant mortality reaches {F(1994, 'IMR'):.1f}", 'out': f"departures exceed arrivals by around {-K(I, out, 'NetMigrations') / 1e6:.1f} million", 'in': f"net arrivals of some {K(I, inn, 'NetMigrations') / 1e6:.1f} million", 'back': f"by {back} the count",
 'sr': f"lowest point in {sl} ({SR(I, sl):.1f}) and stands at {SR(I, y):.1f} now", 'le2': f"gone from {F(2000, 'LEx'):.1f} to {F(y, 'LEx'):.1f} years, {gain(I):.1f} more", 'imr2': f"Infant mortality, {F(2000, 'IMR'):.1f} in 2000, is {F(y, 'IMR'):.1f}",
 'tfr': f"reached {F(tmax, 'TFR'):.2f} in {tmax}; it is {F(y, 'TFR'):.2f} today", 'urb': f"made up {p1(U[1990])} in 1990 and {p1(U[y])} today, with a majority projected for {half}",
 'ld': f"loses {lost / 1e6:.1f} million between the 1993 and 1995 mid-year estimates, ending at {m(P(I, 1995))}",
}
sys.exit(run('rwanda', I, exp, ['population (millions)', 'ld'], yrs) > 0)
