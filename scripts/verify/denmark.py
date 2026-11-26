# Run after `npm run build`: python3 scripts/verify/denmark.py
# Independent check of every figure on /population/denmark/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'DNK'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/denmark.json'))['tableYears']
assert sorted(countries(y, 1e6, EUROPE), key=lambda k: -urban(k)[1950])[:3] == ['GBR', 'DEU', I]
assert [yr for yr in range(1951, y + 1) if P(I, yr) < P(I, yr - 1)] == [1981, 1982, 1983, 1984]
nat = lambda yr: K(I, yr, 'Births') - K(I, yr, 'Deaths')
assert [yr for yr in range(1950, y + 1) if nat(yr) < 0] == list(range(1981, 1989)) + [2022] and all(nat(yr) < 0 for yr in range(2027, 2101))
NM = lambda yr: K(I, yr, 'NetMigrations'); assert all(NM(yr) > 0 for yr in range(1990, 2101)) and max(R, key=NM) == 2022
assert max(R, key=lambda yr: P(I, yr)) == 2042 and 0.96 < P(I, 2100) / P(I, y) < 0.98 and 1.35 < P(I, y) / P(I, 1950) < 1.45
assert sorted(countries(y, 1e6, {'924'}), key=lambda k: -P(k, y))[:3] == ['GBR', 'SWE', I]
exp = exp_base(I, y, U) | {
 'u50': f"{p1(U[1950])} of Danes lived in towns", 'mig': f"The surplus was {c(NM(2015))} in 2015 and peaked at {c(NM(2022))} in 2022; for 2026 it is {c(NM(y))}",
 'pk': f"reaching {m(P(I, 2042))} in 2042, then drifts down to {m(P(I, 2100))} by 2100",
 'ld': f"The 2026 surplus is {c(NM(y))}; the 2022 one, the largest, {c(NM(2022))}",
}
sys.exit(run('denmark', I, exp, ['population (millions)', 'ld'], yrs) > 0)
