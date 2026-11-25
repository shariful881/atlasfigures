# Run after `npm run build`: python3 scripts/verify/ukraine.py
# Independent check of every figure on /population/ukraine/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101); EST = range(1950, 2024)
I = 'UKR'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/ukraine.json'))['tableYears']
peak = max(R, key=lambda yr: P(I, yr)); assert peak == 1993 and 0.23 < 1 - P(I, y) / P(I, peak) < 0.27
assert all(F(yr, 'NatChange') < 0 for yr in range(1991, 2101)) and F(1990, 'NatChange') >= 0
big = countries(y, 5e6); assert min(big, key=lambda k: f(k, y, 'NatChange') / f(k, y, 'TPopulation1July')) == I
W = [k for k in raw if k != 'WORLD']; worst = min(((f(k, yr, 'NetMigrations'), k, yr) for k in W for yr in EST if yr in raw[k])); assert worst[1:] == (I, 2022)
tlow = min(R, key=lambda yr: F(yr, 'TFR')); assert tlow == 2022 and min(countries(2022, 0, EUROPE), key=lambda k: f(k, 2022, 'TFR')) == I
below = max(yr for yr in R if F(yr, 'TFR') >= 2.1) + 1; bt = max(EST, key=lambda yr: F(yr, 'Births')); assert bt == 1960 and F(y, 'Births') < F(bt, 'Births') / 3
assert sorted(countries(y, 0, {'923'}), key=lambda k: -P(k, y))[:2] == ['RUS', I]
pa = next(yr for yr in range(y + 1, 2101) if P('POL', yr) > P(I, yr)); assert pa == 2042 and all(P('POL', yr) > P(I, yr) for yr in range(pa, 2101))
assert P('POL', 2023) > P(I, 2023) and P('POL', 2024) > P(I, 2024) and P('POL', 2025) < P(I, 2025)
exp = exp_base(I, y, U) | {
 'peak': f"{m(P(I, peak))})", 'peak year': f"{peak} peak", 'nat gap': k1(-K(I, y, 'NatChange')), 'since': f"from {1990 + 1} onward",
 'out 2022': f"about {m(-K(I, 2022, 'NetMigrations'))}", 'in 2024': f"2024 (about {m(K(I, 2024, 'NetMigrations'))})", 'in 2025': f"2025 (about {m(K(I, 2025, 'NetMigrations'))})",
 'net 2026': k1(-K(I, y, 'NetMigrations')), 'tfr low': f"{F(tlow,'TFR'):.2f} children per woman", 'below': f"2.1 from {below} on",
 'births now': k1(K(I, y, 'Births')), 'births 1960': f"{k1(K(I, bt, 'Births'))} born in {bt}",
 'pop 2100': m(P(I, 2100)), 'rank 2100': ordn(rank(I, 2100)), 'pop 2050': m(P(I, 2050)), 'pol': f"again in {pa}",
 'median 2100': f"{F(2100,'MedianAgePop'):.1f} for 2100", 'per day': c(abs(K(I, y, 'PopChange')) / 365),
 'peak (m)': m(P(I, peak)), 'tfr lo': f"{F(tlow,'TFR'):.2f}",
}
sys.exit(run('ukraine', I, exp, ['population (millions)', 'tfr', 'peak (m)', 'tfr lo'], yrs) > 0)
