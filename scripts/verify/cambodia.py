# Run after `npm run build`: python3 scripts/verify/cambodia.py
# Independent check of every figure on /country/cambodia/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'KHM'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/cambodia.json'))['tableYears']
SEA = {'920'}
pre = max(range(1950, 1976), key=lambda yr: P(I, yr)); lo = min(range(1975, 1986), key=lambda yr: P(I, yr)); back = next(yr for yr in range(lo + 1, 2101) if P(I, yr) > P(I, pre))
assert (pre, lo, back) == (1974, 1979, 1988) and all(P(I, yr) < P(I, yr - 1) for yr in range(1975, 1980)) and all(P(I, yr) > P(I, yr - 1) for yr in range(1980, y + 1))
assert 0.23 < (P(I, pre) - P(I, lo)) / P(I, pre) < 0.27 and P(I, y) > 3 * P(I, lo)
ll = min(R, key=lambda yr: F(yr, 'LEx')); assert ll == 1977 and F(1975, 'LEx') < 15 and F(1978, 'LEx') < 15 and F(1979, 'LEx') > 40
bl = min(range(1974, 1981), key=lambda yr: K(I, yr, 'Births')); bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert (bl, bt) == (1977, 1994) and K(I, bl, 'Births') < 0.55 * K(I, 1974, 'Births')
sl = min(R, key=lambda yr: SR(I, yr)); assert sl == 1980; assert all(K(I, yr, 'NetMigrations') > 0 for yr in range(1992, 1998)); inn = max(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert inn == 1996
assert max(countries(y, 0, SEA), key=lambda k: f(k, y, 'LEx') - f(k, 2000, 'LEx')) == I and U[y] > 1.9 * U[2010] and sorted(countries(y, 0, SEA), key=lambda k: -P(k, y)).index(I) == 6
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 2078
exp = exp_base(I, y, U) | {
 'low': f"outnumber the {m(P(I, lo))} of {lo}", 'fall': f"from a mid-year estimate of {m(P(I, pre))} in 1974 down to {m(P(I, lo))} by {lo}", 'back': f"passed its 1974 level in {back}",
 'le': f"drops from {F(1974, 'LEx'):.1f} in 1974 to {F(ll, 'LEx'):.1f} in {ll} and returns to {F(1979, 'LEx'):.1f} in 1979", 'births': f"drop to {k1(K(I, bl, 'Births'))} by {bl}",
 'bt': f"high in {bt} (roughly {k1(K(I, bt, 'Births'))})", 'in': f"{inn} the busiest at some {k1(K(I, inn, 'NetMigrations'))}", 'sr': f"low in {sl}, {SR(I, sl):.1f} males to 100 females, and is {SR(I, y):.1f} today",
 'le2': f"lengthened from {F(2000, 'LEx'):.1f} to {F(y, 'LEx'):.1f} years since 2000", 'imr': f"cut from {F(2000, 'IMR'):.1f} to {F(y, 'IMR'):.1f}", 'urb': f"{p1(U[y])} of Cambodians are urban, against {p1(U[2010])} in 2010",
 'peak': f"highest point is {m(P(I, pk))} in {pk}", 'ld': f"shrank by {(P(I, pre) - P(I, lo)) / 1e6:.1f} million between 1974 and 1979, to {m(P(I, lo))}",
}
sys.exit(run('cambodia', I, exp, ['population (millions)', 'ld'], yrs) > 0)
