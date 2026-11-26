# Run after `npm run build`: python3 scripts/verify/south-sudan.py
# Independent check of every figure on /population/south-sudan/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'SSD'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/south-sudan.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7)
falls = [yr for yr in range(1951, 2024 + 3) if P(I, yr) < P(I, yr - 1)]; assert falls == [1988, 1989, 2015, 2016, 2017, 2018]
lo = min(R, key=lambda yr: F(yr, 'LEx')); assert lo == 1988 and F(lo, 'LEx') < 12 and sorted(countries(1988), key=lambda k: f(k, 1988, 'LEx'))[0] == I
im = max(R, key=lambda yr: F(yr, 'IMR')); assert im == 1988 and K(I, 1988, 'Deaths') > 2 * K(I, 1989, 'Deaths')
osum = -sum(K(I, yr, 'NetMigrations') for yr in range(2014, 2018)); assert 1.9e6 < osum < 2e6
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert (out, inn) == (2017, 2023)
back = next(yr for yr in range(2015, 2101) if P(I, yr) > P(I, 2014)); assert back == 2023
assert sorted(ALL, key=lambda k: f(k, y, 'LEx'))[:3] == ['NGA', 'TCD', I] and sorted(ALL, key=lambda k: -f(k, y, 'IMR')).index(I) == 5
assert sorted(ALL, key=lambda k: -(f(k, 2010, 'LEx') - f(k, 1990, 'LEx')))[0] == I and sorted(B, key=lambda k: urban(k)[y]).index(I) == 4
assert max(R, key=lambda yr: P(I, yr)) == 2100 and P(I, 2100) > 1.9 * P(I, y)
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1987; r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert r21 == 2076
exp = exp_base(I, y, U) | {
 'le88': f"estimated at {F(1988, 'LEx'):.1f} years, the lowest anywhere that year, down from {F(1986, 'LEx'):.1f} in 1986", 'imr88': f"{F(1988, 'IMR'):.1f} of every 1,000 babies", 'd88': f"the death count, {c(K(I, 1988, 'Deaths'))}, is more than double",
 'out': f"About {osum / 1e6:.1f} million more left than arrived from 2014 to 2017", 'outtop': f"largest net outflow, {c(-K(I, out, 'NetMigrations'))}, in {out}", 'in': f"biggest net inflow, {c(K(I, inn, 'NetMigrations'))}, falls in {inn}", 'p14': f"beat the 2014 mark ({m(P(I, 2014))})",
 'gain': f"climbed from {F(1990, 'LEx'):.1f} to {F(2010, 'LEx'):.1f} years", 'imr': f"with {F(y, 'IMR'):.1f} infant deaths", 'fut': f"passes {m(P(I, 2050))} by 2050, then reaches {m(P(I, 2100))}", 'tfr': f"topped out in {tmax} ({F(tmax, 'TFR'):.2f} per woman); it is {F(y, 'TFR'):.2f} now and not projected below 2.1 until {r21}",
 'ld': f"Around {osum / 1e6:.1f} million net, over four years",
}
sys.exit(run('south-sudan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
