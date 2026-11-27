# Run after `npm run build`: python3 scripts/verify/yemen.py
# Independent check of every figure on /country/yemen/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
I = 'YEM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/yemen.json'))['tableYears']
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1985
# highest fertility of any country or area in any UN year
assert all(f(k, yr, 'TFR') <= F(tmax, 'TFR') for k in countries(y) for yr in R)
assert 9 < P(I, y) / P(I, 1950) < 10
WAS = {'922'}
assert sorted(countries(y, 0, WAS), key=lambda k: -P(k, y))[:3] == ['TUR', 'IRQ', I]
assert sorted(countries(2100, 0, WAS), key=lambda k: -P(k, 2100))[:3] == [I, 'IRQ', 'SAU']
below = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert below == 2081
assert all(P(I, yr) > P(I, yr - 1) for yr in range(2024, 2101)) and F(1980, 'TFR') > 8 and F(1990, 'TFR') > 8
assert F(1990, 'PopGrowthRate') > F(y, 'PopGrowthRate') + 0.8 and F(y, 'NetMigrations') < 0
exp = exp_base(I, y, U) | {
 'tfr max': f"{tmax} fertility of {F(tmax, 'TFR'):.2f}", 'tfr below': f"above 2.1 until {below}",
 'births': f"from {m(K(I, 2010, 'Births'))} in 2010 to about {m(K(I, y, 'Births'))} now",
 'pop 1950': f"when Yemen had {m(P(I, 1950))}", 'nat': f"deaths by roughly {m(K(I, y, 'NatChange'))}", 'mig': f"net outflow near {k1(-K(I, y, 'NetMigrations'))}",
 'LE 1950': f"about {F(1950, 'LEx'):.1f} years", 'urban 1950': f"{p1(U[1950])} in 1950",
 'pop 2050': f"{m(P(I, 2050))} in 2050", 'pop 2100': f"{m(P(I, 2100))} in 2100", 'growth 1990': f"down from {p1(F(1990, 'PopGrowthRate'))} in 1990",
 'change': f"roughly {m(K(I, y, 'PopChange'))} extra people", 'LE 2050': f"{F(2050, 'LEx'):.1f}",
}
sys.exit(run('yemen', I, exp, ['population (millions)', 'growth 1990'], yrs) > 0)
