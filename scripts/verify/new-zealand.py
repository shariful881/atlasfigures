# Run after `npm run build`: python3 scripts/verify/new-zealand.py
# Independent check of every figure on /population/new-zealand/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101); EST = range(1950, 2024)
I = 'NZL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/new-zealand.json'))['tableYears']
assert 0.85 < F(y, 'NetMigrations') / F(y, 'NatChange') < 1 and f('AUS', y, 'PopGrowthRate') > F(y, 'PopGrowthRate')
out = [yr for yr in EST if F(yr, 'NetMigrations') < 0]
assert out == [1967,1968,1969,1976,1977,1978,1979,1980,1981,1984,1985,1986,1987,1988,1989,1998,1999,2000,2011,2012,2021]
mt = max(EST, key=lambda yr: F(yr, 'NetMigrations')); assert mt == 2016
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1961 and all(1.85 < F(yr, 'TFR') < 2.25 for yr in range(1978, 2011))
peak = max(R, key=lambda yr: P(I, yr)); nd = next(yr for yr in R if F(yr, 'NatChange') < 0); assert peak == 2078 and nd == 2047
OCE = {'927', '928', '954', '957'}; assert sorted(countries(y, 0, OCE), key=lambda k: -P(k, y))[:3] == ['AUS', 'PNG', I]
no = next(yr for yr in range(y + 1, 2101) if P(I, yr) > P('NOR', yr)); assert no == 2063
assert F(1980, 'NetMigrations') < 0 and F(2000, 'NetMigrations') < 0 and all(F(yr, 'NetMigrations') > 0 for yr in yrs if yr > 2023)
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(K(I, y, 'PopChange') / 365), 'nat': f"by about {k1(K(I, y, 'NatChange'))}", 'mig': f"departures by about {k1(K(I, y, 'NetMigrations'))}",
 'change': k1(K(I, y, 'PopChange')), 'out years': f"in {len(out)} separate years", 'mig max': f"about {k1(K(I, mt, 'NetMigrations'))} in {mt}", 'net 2021': f"−{round(-K(I,2021,'NetMigrations')/1000)}k",
 'tfr max': f"{tmax} high of {F(tmax,'TFR'):.2f}", 'tfr 2008': f"{F(2008,'TFR'):.2f} in 2008", 'tfr 2010': f"{F(2010,'TFR'):.2f} in 2010", 'tfr 2018': f"{F(2018,'TFR'):.2f} in 2018",
 'nd': f"From {nd}", 'peak': f"{m(P(I, peak))} in {peak}", 'pop 2100': f"{m(P(I, 2100))} in 2100", 'norway': f"Norway, in {no}",
 'times': f"{P(I, y) / P(I, 1950):.1f} times", 'pop 1950': f"({m(P(I, 1950))})", 'peak (m)': m(P(I, peak)),
}
sys.exit(run('new-zealand', I, exp, ['population (millions)', 'tfr', 'peak (m)'], yrs) > 0)
