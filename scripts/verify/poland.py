# Run after `npm run build`: python3 scripts/verify/poland.py
# Independent check of every figure on /population/poland/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101); EST = range(1950, 2024)
I = 'POL'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/poland.json'))['tableYears']
peak = max(R, key=lambda yr: P(I, yr)); assert peak == 2023 and 0.48 < P(I, 2100) / P(I, peak) < 0.52
last = max(yr for yr in R if F(yr, 'NatChange') >= 0); assert last == 2017
mt = max(EST, key=lambda yr: F(yr, 'NetMigrations')); assert mt == 2022
assert sorted(countries(2022, 0, EUROPE), key=lambda k: -f(k, 2022, 'NetMigrations'))[:2] == ['DEU', I]
assert all(F(yr, 'NetMigrations') < 0 for yr in range(2023, y + 1))
below = next(yr for yr in R if F(yr, 'TFR') < 2.1); assert below == 1989 and all(F(yr, 'TFR') < 2.1 for yr in range(below, 2101))
tlow = min(R, key=lambda yr: F(yr, 'TFR')); bt = max(EST, key=lambda yr: F(yr, 'Births')); assert bt == 1957
assert sorted(countries(y, 10e6, EUROPE), key=lambda k: urban(k)[y])[:2] == ['ROU', I]
assert sorted(countries(y, 0, {'923'}), key=lambda k: -P(k, y))[:3] == ['RUS', 'UKR', I]
exp = exp_base(I, y, U) | {
 'peak': f"{peak} high of {m(P(I, peak))}", 'since': f"since {last + 1}", 'nat gap': k1(-K(I, y, 'NatChange')), 'births': f"{k1(K(I, y, 'Births'))} births", 'deaths': f"{k1(K(I, y, 'Deaths'))} deaths",
 'pop 2050': f"{m(P(I, 2050))} for 2050", 'pop 2100': m(P(I, 2100)), 'net 2021': f"about {k1(K(I, 2021, 'NetMigrations'))} in 2021", 'net 2022': f"{k1(K(I, 2022, 'NetMigrations'))} in 2022",
 'out 2024': f"{k1(-K(I, 2024, 'NetMigrations'))} in 2024", 'out 2025': f"{k1(-K(I, 2025, 'NetMigrations'))} in 2025",
 'below': f"2.1 since {below}", 'tfr low': f"{F(tlow,'TFR'):.2f}, came in {tlow}", 'births 1957': f"{k1(K(I, bt, 'Births'))} in {bt}",
 'median 2000': f"{F(2000,'MedianAgePop'):.1f} in 2000", 'median 2050': f"{F(2050,'MedianAgePop'):.1f} by 2050", 'rank 2050': ordn(rank(I, 2050)) + ' by 2050', 'rank 2100': ordn(rank(I, 2100)),
 'per day': c(abs(K(I, y, 'PopChange')) / 365), 'peak (m)': m(P(I, peak)), 'n22': k1(K(I, 2022, 'NetMigrations')), 'tlow': f"{F(tlow,'TFR'):.2f}",
}
sys.exit(run('poland', I, exp, ['population (millions)', 'tfr', 'peak (m)', 'pop 2100', 'n22', 'tlow'], yrs) > 0)
