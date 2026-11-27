# Run after `npm run build`: python3 scripts/verify/kazakhstan.py
# Independent check of every figure on /country/kazakhstan/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'KAZ'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/kazakhstan.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7)
hi = max(range(1980, 2000), key=lambda yr: P(I, yr)); lo = min(range(hi + 1, 2010), key=lambda yr: P(I, yr)); back = next(yr for yr in range(hi + 1, 2101) if P(I, yr) > P(I, hi))
assert (hi, lo, back) == (1992, 1999, 2013) and [yr for yr in range(1950, 2100) if K(I, yr, 'PopChange') < 0] == list(range(1992, 1999))
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 1994
assert [yr for yr in range(1990, y + 1) if F(yr, 'TFR') < 2.1] == list(range(1996, 2004))
tl = min(range(1990, y + 1), key=lambda yr: F(yr, 'TFR')); th = max(range(2000, y + 1), key=lambda yr: F(yr, 'TFR')); assert (tl, th) == (2000, 2021)
assert max(ALL, key=lambda k: f(k, 2020, 'TFR') - f(k, 2000, 'TFR')) == I
bl = min(range(1985, 2010), key=lambda yr: K(I, yr, 'Births')); bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert (bl, bt) == (1999, 2021)
assert sorted(B, key=lambda k: f(k, y, 'PopDensity'))[:3] == ['AUS', 'CAN', I] and sorted(ALL, key=lambda k: -land(k)).index(I) == 8
assert all(SR(I, yr) < 100 for yr in range(1950, 2087)) and SR(I, 2087) > 100; sl = min(R, key=lambda yr: SR(I, yr)); assert sl == 2000
ut = max(range(1950, 2000), key=lambda yr: U[yr]); ul = min(range(1990, y + 1), key=lambda yr: U[yr]); ub = next(yr for yr in range(2001, 2051) if U[yr] > U[ut]); assert (ut, ul, ub) == (1989, 2009, 2017)
assert next(yr for yr in R if P('UZB', yr) > P(I, yr)) == 1977 and P(I, 2100) > P(I, 2099)
exp = exp_base(I, y, U) | {
 'low': f"well above the {m(P(I, lo))} of {lo}", 'hi': f"It hit {m(P(I, hi))} in {hi}", 'out': f"{out} saw the most net departures, around {k1(-K(I, out, 'NetMigrations'))}", 'back': f"Only in {back} did the count exceed",
 'tfr': f"bottoming out at {F(tl, 'TFR'):.2f} in {tl}, then climbed to {F(th, 'TFR'):.2f} in {th}; it is {F(y, 'TFR'):.2f} now", 'births': f"{k1(K(I, bl, 'Births'))} were born in {bl}, {k1(K(I, bt, 'Births'))} in {bt}",
 'sr': f"widest in {sl}, at {SR(I, sl):.1f} men per 100 women, and has narrowed to {SR(I, y):.1f}", 'le': f"dipped from {F(1990, 'LEx'):.1f} in 1990 to {F(2000, 'LEx'):.1f} in 2000, has since reached {F(y, 'LEx'):.1f}",
 'urban': f"rose to {p1(U[ut])} by {ut}, slid to {p1(U[ul])} by {ul} and climbed back above the {ut} figure in {ub}; today it is {p1(U[y])}", 'uzb': f"since 1977", 'p2100': f"when {m(P(I, 2100))} live there",
 'ld': f"the 1 July count slid from {m(P(I, hi))} ({hi}) to a {lo} low of {m(P(I, lo))}",
}
sys.exit(run('kazakhstan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
