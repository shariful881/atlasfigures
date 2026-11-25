# Run after `npm run build`: python3 scripts/verify/iran.py
# Independent check of every figure on /population/iran/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y])}
I = 'IRN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
drop = F(1980, 'TFR') - F(2000, 'TFR'); assert sorted(countries(y, 10e6), key=lambda k: -(f(k, 1980, 'TFR') - f(k, 2000, 'TFR')))[0] == I and drop > 4.5
below = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1); assert below == 1999 and all(F(yr, 'TFR') < 2.1 for yr in range(1999, 2101)) and max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')) == 1959
btop = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert btop == 1985 and 0.5 < K(I, y, 'Births') / K(I, btop, 'Births') < 0.55
peak = max(range(1950, 2101), key=lambda yr: P(I, yr)); nl = next(yr for yr in range(1950, 2101) if F(yr, 'NatChange') < 0); assert all(K(I, yr, 'PopChange') < 0 for yr in range(peak + 1, 2101))
back = next(yr for yr in range(1950, 2101) if P(I, yr) >= P(I, 2100))
assert [yr for yr in range(1950, 2024) if K(I, yr, 'PopChange') < 0] == [1993] and K(I, y, 'NatChange') > K(I, y, 'PopChange') / 2
S = countries(y, 0, {'5501'}); assert sorted(S, key=lambda k: -P(k, y))[:4] == ['IND', 'PAK', 'BGD', I] and sorted(S, key=lambda k: -f(k, y, 'LEx'))[:2] == ['MDV', I]
exp = exp_base(I, y, U) | {
 'growth (+)': '+' + p1(F(y, 'PopGrowthRate')), 'per day': c(K(I, y, 'PopChange') / 365), 'change (thousand)': k1(K(I, y, 'PopChange')),
 'tfr 1980': f"{F(1980,'TFR'):.2f}", 'tfr 1990': f"{F(1990,'TFR'):.2f}", 'tfr 2000': f"{F(2000,'TFR'):.2f}", 'drop': f"{drop:.2f}", 'below 2.1': f"below 2.1 in {below}", 'tfr': f"{F(y,'TFR'):.2f}",
 'births record': f"{m(K(I, btop, 'Births'))}, in {btop}", 'births': m(K(I, y, 'Births')), 'median 2000': f"{F(2000,'MedianAgePop'):.1f}", 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
 'peak': f"In {peak}, at {m(P(I, peak))}", 'peak (FAQ)': f"after {peak}, when it reaches a projected {m(P(I, peak))}", 'natural loss': str(nl), 'pop 2100': m(P(I, 2100)), 'back to': str(back), 'outflow 1993': m(-K(I, 1993, 'NetMigrations')),
 'LE': f"{F(y,'LEx'):.1f}", 'LE 1950': f"{F(1950,'LEx'):.1f}",
}
sys.exit(run('iran', I, exp, ['population (millions)', 'tfr 1980', 'tfr 2000', 'drop', 'peak (FAQ)', 'LE'], yrs) > 0)
