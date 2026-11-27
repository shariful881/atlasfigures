# Run after `npm run build`: python3 scripts/verify/kyrgyzstan.py
# Independent check of every figure on /country/kyrgyzstan/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'KGZ'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/kyrgyzstan.json'))['tableYears']
cas = countries(y, 1e6, {'5500'})
NM = lambda yr: K(I, yr, 'NetMigrations')
assert min(R, key=NM) == 1993 and -NM(1993) > 1e5 and all(NM(yr) < 0 for yr in range(1990, 2000)) and all(NM(yr) >= 0 for yr in range(2016, 2027)) and next(yr for yr in range(2027, 2101) if NM(yr) < 0) == 2028 and max(R, key=NM) == 2020
lo = min(range(1990, 2011), key=lambda yr: F(yr, 'TFR')); hi = max(range(2001, y + 1), key=lambda yr: F(yr, 'TFR')); assert (lo, hi) == (2001, 2019) and F(y, 'TFR') < F(hi, 'TFR')
bt = max(R, key=lambda yr: K(I, yr, 'Births')); ut = max(range(1950, 2051), key=lambda yr: U[yr]); rp = next(yr for yr in R if yr > y and F(yr, 'TFR') < 2.1)
assert (bt, ut, rp) == (2019, 1979, 2061) and all(U[yr] < 50 for yr in range(1950, 2051)) and sorted(cas, key=lambda k: urban(k)[y])[:2] == ['TJK', I]
assert all(P(I, yr) > P(I, yr - 1) for yr in range(y, 2101)) and P(I, y) / P(I, 1950) > 4
exp = exp_base(I, y, U) | {
 'mig': f"{c(-NM(1992))} in 1992 and most of all {c(-NM(1993))} in 1993", 'in': f"reaching {c(NM(2020))} in 2020", 'box': f"{c(-NM(2010))}", 'sr': f"from {SR(I, 1990):.1f} in 1990 to {SR(I, y):.1f} today",
 'tfr': f"{F(lo, 'TFR'):.2f} per woman in 2001, {F(hi, 'TFR'):.2f} by 2019, and {F(y, 'TFR'):.2f} now", 'b': f"Kyrgyz births hit their record, {c(K(I, bt, 'Births'))}, in 2019",
 'u': f"peaked in 1979 at {p1(U[ut])}; it has a current level of {p1(U[y])}", 'fut': f"{m(P(I, 2050))} around 2050, then {m(P(I, 2100))} when the century closes",
 'ld': f"the biggest loss, {c(-NM(1993))}, came in 1993",
}
assert NM(2010) < 0
sys.exit(run('kyrgyzstan', I, exp, ['population (millions)', 'ld'], yrs) > 0)
