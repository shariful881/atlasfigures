# Run after `npm run build`: python3 scripts/verify/turkmenistan.py
# Independent check of every figure on /country/turkmenistan/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'TKM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/turkmenistan.json'))['tableYears']
cas = countries(y, 1e6, {'5500'})
assert all(42 < U[yr] < 48.5 for yr in range(1950, 2051))
assert max(cas, key=lambda k: f(k, y, 'IMR')) == I and min(cas, key=lambda k: f(k, y, 'LEx')) == I
assert sorted(cas, key=lambda k: f(k, y, 'PopDensity'))[:2] == ['KAZ', I] and sorted(cas, key=lambda k: -P(k, y) / P(k, 1950))[:2] == ['TJK', I]
assert all(K(I, yr, 'NetMigrations') <= 0 for yr in range(1990, 1999)) and K(I, y, 'NetMigrations') > 0
tm = max(R, key=lambda yr: F(yr, 'TFR')); rp = next(yr for yr in R if yr > y and F(yr, 'TFR') < 2.1); bt = max(R, key=lambda yr: K(I, yr, 'Births')); pk = max(R, key=lambda yr: P(I, yr))
assert (tm, bt, pk) == (1963, 2016, 2079) and 6 < P(I, y) / P(I, 1950) < 6.2
exp = exp_base(I, y, U) | {
 'u': f"the share was {p1(U[1950])} in 1950 and {p1(U[1970])} in 1970; the 2026 reading is {p1(U[y])} and the 2050 one {p1(U[2050])}",
 'h': f"infant mortality ({F(y, 'IMR'):.1f} for every 1,000 born) and its shortest life expectancy ({F(y, 'LEx'):.1f} years)",
 'b': f"they peaked at {c(K(I, bt, 'Births'))} in 2016 and are projected at {c(K(I, y, 'Births'))} this year", 'tfr': f"Fertility peaked at {F(tm, 'TFR'):.2f} (1963); today's rate is {F(y, 'TFR'):.2f} and 2.1 arrives in {rp}",
 'mig': f"{c(K(I, y, 'NetMigrations'))} in 2026", 'pk': f"It climbs to {m(P(I, pk))} by 2079, then dips slightly to {m(P(I, 2100))} by 2100",
 'ld': f"It was {p1(U[1950])} then, is {p1(U[y])} now and should be {p1(U[2050])} by 2050",
}
sys.exit(run('turkmenistan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
