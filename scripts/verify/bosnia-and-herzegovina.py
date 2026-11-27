# Run after `npm run build`: python3 scripts/verify/bosnia-and-herzegovina.py
# Independent check of every figure on /country/bosnia-and-herzegovina/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
fromTop = lambda k: P(k, y) / max(P(k, yr) for yr in range(1950, y + 1))
I = 'BIH'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/bosnia-and-herzegovina.json'))['tableYears']
NM = lambda yr: K(I, yr, 'NetMigrations'); b1 = countries(y, 1e6)
assert max(R, key=lambda yr: P(I, yr)) == 1991 and min(R, key=NM) == 1992 and 0.095 < -NM(1992) / P(I, 1991) < 0.1 and max(R, key=NM) == 1996
assert all(P(I, yr) < P(I, yr - 1) for yr in list(range(1992, 1996)) + list(range(2003, 2101))) and all(P(I, yr) > P(I, yr - 1) for yr in range(1996, 2003))
assert all(NM(yr) > 0 for yr in range(1995, 2002)) and NM(1994) < 0 and NM(2002) < 0
assert sorted(b1, key=fromTop)[:4] == ['MDA', 'LVA', 'GEO', I] and fromTop(I) < 0.7 and sorted(b1, key=lambda k: -f(k, y, 'MedianAgePop')).index(I) == 8
assert min(range(1950, y + 1), key=lambda yr: K(I, yr, 'Births')) == y and all(K(I, yr, 'Deaths') > K(I, yr, 'Births') for yr in range(2010, 2101)) and 0.43 < P(I, 2100) / P(I, y) < 0.45
exp = exp_base(I, y, U) | {
 'out': f"Net departures reached {c(-NM(1992))} in 1992, close to 10% of the 1991 count, followed by {c(-NM(1993))} in 1993",
 'le': f"Lifespan estimates sink from {F(1991, 'LEx'):.1f} (1991) to {F(1992, 'LEx'):.1f} and then {F(1993, 'LEx'):.1f}", 'p95': f"By 1995 the total stood at {m(P(I, 1995))}",
 'in': f"peaking at {c(NM(1996))} in 1996", 'p02': f"reaching {m(P(I, 2002))}", 'nat': f"The {c(K(I, y, 'Births'))} births expected in 2026 are the fewest of any year on file, against {c(K(I, y, 'Deaths'))} deaths",
 'fut': f"passes {m(P(I, 2050))} in 2050 and lands at {m(P(I, 2100))} in 2100", 'pk': f"well short of the 1991 peak, {m(P(I, 1991))}",
 'ld': f"{c(-NM(1992))}, close to 10% of the 1991 total",
}
sys.exit(run('bosnia-and-herzegovina', I, exp, ['population (millions)', 'ld'], yrs) > 0)
