# Run after `npm run build`: python3 scripts/verify/sudan.py
# Independent check of every figure on /population/sudan/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101); EST = range(1950, 2024)
I = 'SDN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/sudan.json'))['tableYears']
afr = sorted(countries(y, 0, AFRICA), key=lambda k: -P(k, y)); nafr = sorted(countries(y, 0, {'912'}), key=lambda k: -P(k, y))
assert afr.index(I) == 7 and nafr[:2] == ['EGY', I]
out23 = sorted(countries(2023), key=lambda k: f(k, 2023, 'NetMigrations')); assert out23[:2] == ['PAK', I]
assert min(EST, key=lambda yr: F(yr, 'NetMigrations')) == 2023
assert 0 < K(I, 2023, 'PopChange') < 20000 and F(2025, 'NetMigrations') > 0 and F(y, 'NetMigrations') > 0
assert all(P(I, yr) > P(I, yr - 1) for yr in range(1951, 2101))
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1971 and all(F(yr, 'TFR') >= 2.1 for yr in R)
p100 = next(yr for yr in R if P(I, yr) > 1e8); assert p100 == 2062
assert U[2050] - U[y] < 1.5 and U[y] < 50
exp = exp_base(I, y, U) | {
 'out 2023': f"Some {m(-K(I, 2023, 'NetMigrations'))} more people left", 'nat 2023': f"about {m(K(I, 2023, 'NatChange'))} more births than deaths",
 'change 2023': f"rise of just {k1(K(I, 2023, 'PopChange'))}", 'growth 2022': f"growth of {p1(F(2022, 'PopGrowthRate'))} the year before",
 'mig 2025': f"roughly {k1(K(I, 2025, 'NetMigrations'))} for 2025", 'mig 2026': f"{k1(K(I, y, 'NetMigrations'))} for 2026",
 'pop 2050': f"{m(P(I, 2050))} by mid-century", 'pop 2100': f"{m(P(I, 2100))} at its end", 'rank 2100': f"to {ordn(rank(I, 2100))}",
 'pop 2075': f"by 2075 it shows {m(P(I, 2075))}", 'pass 100m': f"crosses that mark in {p100}",
 'times': f"about {P(I, y) / P(I, 1950):.1f}-fold", 'pop 1950': f"({m(P(I, 1950))} then)",
 'tfr max': f"down from {F(tmax, 'TFR'):.2f} at the {tmax} high", 'tfr 2100': f"projected rate is {F(2100, 'TFR'):.2f}",
 'end century': f"ends the century at {m(P(I, 2100))}", 'births': f"about {m(K(I, y, 'Births'))} births in 2026", 'urban 1950': f"from {p1(U[1950])} in 1950", 'urban 2050': f"({p1(U[2050])})",
}
sys.exit(run('sudan', I, exp, ['population (millions)', 'end century', 'pop 2075', 'mig 2025'], yrs) > 0)
