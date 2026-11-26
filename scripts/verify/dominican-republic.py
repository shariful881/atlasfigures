# Run after `npm run build`: python3 scripts/verify/dominican-republic.py
# Independent check of every figure on /population/dominican-republic/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'DOM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/dominican-republic.json'))['tableYears']
LAT = {'915', '916', '931'}; L1 = countries(y, 1e6, LAT)
assert all(K(I, yr, 'NetMigrations') < 0 for yr in R); out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 2006
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2061 and 4.8 < P(I, y) / P(I, 1950) < 4.9
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1956 and sorted(L1, key=lambda k: -(f(k, 1956, 'TFR') - f(k, y, 'TFR')))[0] == I
r21 = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert r21 == 2030
ut = max(range(1950, y + 1), key=lambda yr: U[yr]); assert ut == 2011 and U[y] < U[ut] - 1 and U[2050] > 89
assert next(yr for yr in R if SR(I, yr) < 100) == 2003 and all(SR(I, yr) < 100 for yr in range(2003, 2101))
assert [yr for yr in R if P(I, yr) > P('HTI', yr)] == list(range(1977, 2013))
bt = max(R, key=lambda yr: K(I, yr, 'Births')); assert bt == 1993
assert sorted(L1, key=lambda k: -f(k, y, 'IMR'))[:3] == ['HTI', 'BOL', I] and sorted(countries(y, 0, {'915'}), key=lambda k: -P(k, y)).index(I) == 1
exp = exp_base(I, y, U) | {
 '1950': f"its 1950 total of {m(P(I, 1950))}", 'now': f"{c(K(I, y, 'Births'))} born, {c(K(I, y, 'Deaths'))} dying, so a natural gain of {c(K(I, y, 'NatChange'))} that more than covers {c(-K(I, y, 'NetMigrations'))} net departures",
 'out': f"most of all in {out} ({c(-K(I, out, 'NetMigrations'))})", 'pk': f"rising until {pk} and a high of {m(P(I, pk))}", 'tfr': f"it was {F(tmax, 'TFR'):.2f} per woman in {tmax} and is {F(y, 'TFR'):.2f} today, with a drop below 2.1 projected for {r21}",
 'bt': f"topped out at {c(K(I, bt, 'Births'))} in {bt}", 'imr': f"{F(y, 'IMR'):.1f} of every 1,000 die", 'urb': f"rose from {p1(U[1950])} in 1950 to a high of {p1(U[ut])} in {ut}; today it is {p1(U[y])}", 'u50': f"renewed rise, to {p1(U[2050])} by 2050",
 'sr': f"sex ratio of {SR(I, y):.1f}",
 'ld': f"The biggest, {c(-K(I, out, 'NetMigrations'))}, is estimated for {out}",
}
sys.exit(run('dominican-republic', I, exp, ['population (millions)', 'ld'], yrs) > 0)
