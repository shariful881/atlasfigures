# Run after `npm run build`: python3 scripts/verify/namibia.py
# Independent check of every figure on /population/namibia/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NAM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/namibia.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); b1 = countries(y, 1e6)
assert sorted(b1, key=lambda k: f(k, y, 'PopDensity'))[:3] == ['MNG', 'AUS', I] and next(yr for yr in range(1950, 2051) if U[yr] > 50) == 2024
assert all(NM(yr) < 0 for yr in range(1950, 1985)) and all(NM(yr) > 0 for yr in range(1985, 2002)) and all(NM(yr) < 0 for yr in range(2002, 2012)) and NM(2012) > 0
assert max(R, key=NM) == 1989 and min(R, key=NM) == 1978 and abs(NM(y)) < 1000
assert min(range(1970, y + 1), key=lambda yr: F(yr, 'LEx')) == 2003 and all(F(yr, 'LEx') < F(yr - 1, 'LEx') for yr in range(1991, 2002)) and F(2021, 'LEx') < F(2020, 'LEx') - 3 < F(2022, 'LEx')
assert max(R, key=lambda yr: P(I, yr)) == 2100 and next(yr for yr in R if F(yr, 'TFR') < 2.1) == 2074 and 6 < P(I, y) / P(I, 1950) < 6.3
exp = exp_base(I, y, U) | {
 'g': f"about six times the {c(P(I, 1950))} of 1950", 'urb': f"It stood at {p1(U[1950])} in 1950, reads {p1(U[y])} today, and the 2050 projection gives {p1(U[2050])}",
 'le': f"Starting from {F(1990, 'LEx'):.1f} in 1990", 'le2': f"the low point, {F(2003, 'LEx'):.1f}, arrived in 2003", 'le3': f"one-year drop to {F(2021, 'LEx'):.1f}",
 'nm': f"heaviest in 1978 ({c(-NM(1978))}); inflows held over 1985–2001, topped by 1989 with {c(NM(1989))}", 'fut': f"ending at {m(P(I, 2100))}", 'tfr': "2074 the first projected year under 2.1",
 'ld': f"{m(P(I, 2100))}, with {m(P(I, 2050))} along the way around 2050",
}
sys.exit(run('namibia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
