# Run after `npm run build`: python3 scripts/verify/libya.py
# Independent check of every figure on /country/libya/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'LBY'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/libya.json'))['tableYears']
af = countries(y, 1e6, AFRICA); big1 = countries(y, 1e6)
out = min(R, key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 2011 and -K(I, 2011, 'NetMigrations') > 5.5e5
assert [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == [1983, 2011, 2012]
assert max(range(1950, y + 1), key=lambda yr: F(yr, 'TFR')) == 1971 and F(1971, 'TFR') > 8
assert max(big1, key=lambda k: f(k, 1971, 'TFR') - f(k, y, 'TFR')) == I
assert sorted(af, key=lambda k: f(k, y, 'PopDensity'))[:2] == ['NAM', I] and sorted(af, key=lambda k: -urban(k)[y])[:2] == ['GAB', I]
rp = next(yr for yr in R if yr > y and F(yr, 'TFR') < 2.1); pk = max(R, key=lambda yr: P(I, yr)); assert (rp, pk) == (2030, 2086) and 6.6 < P(I, y) / P(I, 1950) < 6.8
exp = exp_base(I, y, U) | {
 'out': f"Departures outnumbered arrivals by {c(-K(I, 2011, 'NetMigrations'))}", 'le11': f"Life expectancy went from {F(2010, 'LEx'):.1f} in 2010 to {F(2011, 'LEx'):.1f}, then returned to {F(2012, 'LEx'):.1f} in 2012",
 'd23': f"Deaths jumped from {c(K(I, 2022, 'Deaths'))} in 2022 to {c(K(I, 2023, 'Deaths'))}, and life expectancy slid from {F(2022, 'LEx'):.1f} to {F(2023, 'LEx'):.1f}",
 'tfr': f"{F(1971, 'TFR'):.2f} that year, {F(y, 'TFR'):.2f} today, with the rate projected under 2.1 from {rp}", 'sr': f"{SR(I, y):.1f} to 100",
 'pk': f"Growth continues until 2086, when the projection reaches {m(P(I, pk))}",
 'ld': f"The UN puts net departures at {c(-K(I, 2011, 'NetMigrations'))} that year",
}
sys.exit(run('libya', I, exp, ['population (millions)', 'ld'], yrs) > 0)
