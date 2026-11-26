# Run after `npm run build`: python3 scripts/verify/niger.py
# Independent check of every figure on /population/niger/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
top = lambda yr: max(ALL, key=lambda k: f(k, yr, 'TFR') if yr in raw[k] else -1)
first = [yr for yr in range(1950, 2024) if top(yr) == I]; assert first == list(range(1995, 2019))
assert sorted(ALL, key=lambda k: -f(k, y, 'TFR'))[:5] == ['TCD', 'SOM', 'COD', 'CAF', I]
tmax = max(R, key=lambda yr: F(yr, 'TFR')); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (tmax, under) == (1985, 2091) and F(2010, 'TFR') - F(y, 'TFR') > 1.95 and all(F(yr, 'TFR') > 7 for yr in (1950, 1960, 1970, 1980, 1990, 2000, 2010, 2015))
B = countries(y, 1e7); assert sorted(B, key=lambda k: f(k, y, 'MedianAgePop'))[:2] == ['SOM', I]
assert sorted(B, key=lambda k: -f(k, y, 'PopGrowthRate')).index(I) <= 2
mf = next(yr for yr in R if SR(I, yr) > 100); assert mf == 1989 and all(SR(I, yr) > 100 for yr in range(mf, y + 1)) and SR(I, 1950) < 85
assert sorted([k for k in B if k in [r[4] for r in _rows]], key=lambda k: urban(k)[y])[:3] == ['PNG', 'MWI', I]
WAF = {'914'}; assert sorted(countries(y, 0, WAF), key=lambda k: -land(k))[0] == I and sorted(countries(2100, 0, WAF), key=lambda k: -P(k, 2100))[:3] == ['NGA', 'CIV', I]
fifty = next(yr for yr in R if P(I, yr) > 5e7); dbl = next(yr for yr in R if P(I, yr) > 2 * P(I, y)); assert (fifty, dbl) == (2048, 2055)
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101))
exp = exp_base(I, y, U) | {
 'n years': f"For {len(first)} consecutive", 'tfr max': f"{F(tmax, 'TFR'):.2f}, belongs to {tmax}", 'tfr 2010': f"still {F(2010, 'TFR'):.2f}", 'under': f"until {under}",
 'births': f"some {m(K(I, y, 'Births'))} births", 'deaths': f"{k1(K(I, y, 'Deaths'))} deaths", 'le': f"{F(1950, 'LEx'):.1f} years in 1950, {F(y, 'LEx'):.1f} today",
 'sr 1950': f"ratio is {SR(I, 1950):.1f} males", 'sr now': f"ratio is {SR(I, y):.1f}", 'sr mf': f"{SR(I, mf):.1f}", 'mf': f"since {mf}",
 'fifty': f"falls in {fifty}", 'dbl': f"by {dbl} the population", 'pop 2100': f"brings {m(P(I, 2100))}", 'rank 2100': f"Niger {ordn(rank(I, 2100))} on",
 'times': f"already {P(I, y) / P(I, 1950):.1f} times", 'ld': f"ranks fifth, after Chad",
}
sys.exit(run('niger', I, exp, ['population (millions)', 'ld'], yrs) > 0)
