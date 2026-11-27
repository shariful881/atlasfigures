# Run after `npm run build`: python3 scripts/verify/north-korea.py
# Independent check of every figure on /country/north-korea/population/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'PRK'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/north-korea.json'))['tableYears']
peak = max(R, key=lambda yr: P(I, yr)); nn = next(yr for yr in range(1961, 2101) if F(yr, 'NatChange') < 0); under = next(yr for yr in R if F(yr, 'TFR') < 2.1)
assert (peak, nn, under) == (2032, 2033, 1996) and all(F(yr, 'TFR') < 2.1 for yr in range(under, 2101))
assert f(I, y, 'TFR') > 2 * f('KOR', y, 'TFR') and sorted(countries(y, 0, {'906'}), key=lambda k: -P(k, y))[:4] == ['CHN', 'JPN', 'KOR', I] and 0.48 < P(I, y) / P('KOR', y) < 0.55
assert all(K(I, yr, 'PopChange') < 0 for yr in (1950, 1951, 1952, 1953)) and K(I, 1954, 'PopChange') > 0
reg = next(yr for yr in range(1954, 2101) if P(I, yr) > P(I, 1950)); assert reg == 1958
assert all(60.5 < F(yr, 'LEx') < 61.5 for yr in range(1995, 2003)) and F(1994, 'LEx') > 70 and F(2003, 'LEx') > 69
assert all(F(yr, 'NetMigrations') == 0 for yr in range(1958, 1994)) and all(-4 < F(yr, 'NetMigrations') < 0 for yr in range(1994, y + 1))
assert (rank(I, 1950), rank(I, y), rank(I, 2100)) == (34, 56, 78)
exp = exp_base(I, y, U) | {
 'peak': f"reaches {m(P(I, peak))}", 'nn': f"From {nn} onward", 'pop 2100': f"leaving {m(P(I, 2100))} in 2100", 'ranks': f"sat {ordn(rank(I, 1950))} on the world list in 1950, sits {ordn(rank(I, y))} today and would drop to {ordn(rank(I, 2100))}",
 'war': f"{m(P(I, 1950))} at the 1950 mid-point against {m(P(I, 1953))} three years later", 'le 1950': f"{F(1950, 'LEx'):.1f} years in 1950", 'reg': f"level by {reg}",
 'le': f"from {F(1994, 'LEx'):.1f} years in 1994 to {F(1995, 'LEx'):.1f} in 1995", 'le 2003': f"{F(2003, 'LEx'):.1f} in 2003", 'deaths': f"about {k1(K(I, 1994, 'Deaths'))} in 1994 to {k1(K(I, 1995, 'Deaths'))}",
 'kor': f"South Korea's {f('KOR', y, 'TFR'):.2f}", 'gap': f"is {f('KOR', y, 'MedianAgePop') - F(y, 'MedianAgePop'):.1f} years lower", 'kor age': f"against {f('KOR', y, 'MedianAgePop'):.1f}",
 'mig': f"about {k1(-K(I, y, 'NetMigrations'))} in 2026", 'under': f"since {under}", 'ld': f"maximum, {m(P(I, peak))}, in {peak}",
}
sys.exit(run('north-korea', I, exp, ['population (millions)', 'ld'], yrs) > 0)
