# Run after `npm run build`: python3 scripts/verify/lesotho.py
# Independent check of every figure on /country/lesotho/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'LSO'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/lesotho.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations')
assert all(F(yr, 'LEx') < F(yr - 1, 'LEx') for yr in range(1996, 2007)) and len(range(1996, 2007)) == 11
assert min(countries(2006, 1e6), key=lambda k: f(k, 2006, 'LEx')) == I and sorted(countries(y, 1e6), key=lambda k: f(k, y, 'LEx')).index(I) == 4
assert all(P(I, yr) < P(I, yr - 1) for yr in range(2001, 2007)) and P(I, 2007) > P(I, 2006) and all(P(I, yr) > P(I, yr - 1) for yr in range(2007, 2084))
assert all(NM(yr) < 0 for yr in range(1986, 2101)) and NM(1985) >= 0 and min(R, key=NM) == 2005
assert next(yr for yr in range(1950, 2051) if U[yr] > 50) == 2031 and max(R, key=lambda yr: K(I, yr, 'Births')) == 1987 and max(R, key=lambda yr: P(I, yr)) == 2083
exp = exp_base(I, y, U) | {
 'le': f"beginning at {F(1995, 'LEx'):.1f} (1995) and ending at {F(2006, 'LEx'):.1f} (2006)", 'p': f"took the count from {m(P(I, 2000))} down to {m(P(I, 2006))}",
 'pk': f"climbs until 2083 ({m(P(I, 2083))})", 'nm': f"heaviest in 2005 at {c(-NM(2005))}; for 2026 the UN expects {c(-NM(y))}",
 'ld': f"2005 saw the largest outflow ({c(-NM(2005))})",
}
sys.exit(run('lesotho', I, exp, ['population (millions)', 'ld'], yrs) > 0)
