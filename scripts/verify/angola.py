# Run after `npm run build`: python3 scripts/verify/angola.py
# Independent check of every figure on /population/angola/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
I = 'AGO'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/angola.json'))['tableYears']
big = countries(y, 1e7, AFRICA)
assert sorted(big, key=lambda k: -urban(k)[y])[:2] == ['DZA', I]
assert sorted(countries(y, 0, {'911'}), key=lambda k: -P(k, y))[:2] == ['COD', I]
assert sorted(countries(2100, 0, AFRICA), key=lambda k: -P(k, 2100)).index(I) == 5 and rank(I, 2100) == 13
assert 8.5 < P(I, y) / P(I, 1950) < 9
tmax = max(R, key=lambda yr: F(yr, 'TFR')); assert tmax == 1974 and all(F(yr, 'TFR') >= 2.1 for yr in R)
assert sorted(countries(y, 1e7), key=lambda k: f(k, y, 'MedianAgePop')).index(I) < 10
assert U[1990] < 50 < U[2000]
exp = exp_base(I, y, U) | {
 'urban 1950': f"up from {p1(U[1950])} in 1950", 'urban 2000': f"{p1(U[2000])} in 2000", 'urban 2050': f"Prospects is {p1(U[2050])}",
 'change': f"Around {m(K(I, y, 'PopChange'))} in 2026", 'births': f"some {m(K(I, y, 'Births'))} births", 'deaths': f"about {k1(K(I, y, 'Deaths'))} deaths",
 'pop 1950': f"when there were {m(P(I, 1950))}", 'tfr max': f"{F(tmax, 'TFR'):.2f} at its {tmax} peak",
 'rank 2100': f"{ordn(rank(I, 2100))} globally and sixth", 'pop 2100': f"{m(P(I, 2100))} people on the medium projection", 'pop 2050': f"({m(P(I, 2050))} in 2050)",
 'ld 2100': f"says {m(P(I, 2100))}",
}
sys.exit(run('angola', I, exp, ['population (millions)', 'ld 2100'], yrs) > 0)
