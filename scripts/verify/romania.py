# Run after `npm run build`: python3 scripts/verify/romania.py
# Independent check of every figure on /population/romania/ against the original UN files.
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'ROU'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/romania.json'))['tableYears']
EEU = {'923'}
pk = max(R, key=lambda yr: P(I, yr)); assert pk == 1991 and all(P(I, yr) < P(I, yr - 1) for yr in range(1992, 2101))
nn = next(yr for yr in R if K(I, yr, 'NatChange') < 0); assert nn == 1993 and all(K(I, yr, 'NatChange') < 0 for yr in range(1993, 2101))
assert F(1966, 'TFR') < 1.9 and F(1967, 'TFR') > 3.5 and K(I, 1967, 'Births') > 1.9 * K(I, 1966, 'Births')
assert max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')) == 1967 and max(R, key=lambda yr: F(yr, 'TFR')) == 1967; tl = min(range(1950, 2024), key=lambda yr: F(yr, 'TFR')); assert tl == 2002
out = min(range(1950, 2024), key=lambda yr: K(I, yr, 'NetMigrations')); assert out == 2008 and [yr for yr in range(1992, 2100) if K(I, yr, 'PopChange') >= 0] == [2022] and K(I, 2022, 'NetMigrations') > 0
b50 = next(yr for yr in range(1992, 2101) if P(I, yr) < P(I, 1950)); assert b50 == 2047; lost = (1 - P(I, y) / P(I, pk)) * 100
assert sorted(countries(y, 0, EEU), key=lambda k: -P(k, y)).index(I) == 3 and sorted(countries(y, 0, EEU), key=lambda k: urban(k)[y])[:2] == ['MDA', I] and max(range(1950, y + 1), key=lambda yr: U[yr]) == 1992
assert sum(K(I, yr, 'NetMigrations') < 0 for yr in R) > 100
exp = exp_base(I, y, U) | {
 'peak': f"topped out at {m(P(I, pk))} in {pk}", 'lost': f"About {(P(I, pk) - P(I, y)) / 1e6:.1f} million, or {lost:.1f}%", 'deaths': f"roughly {k1(K(I, y, 'Deaths'))} deaths and {k1(K(I, y, 'Births'))} births",
 'out': f"heaviest in {out} at about {k1(-K(I, out, 'NetMigrations'))}", 'in22': f"net arrivals came to about {k1(K(I, 2022, 'NetMigrations'))}",
 'tfr': f"jumps from {F(1966, 'TFR'):.2f} in 1966 to {F(1967, 'TFR'):.2f} in 1967", 'births': f"leap to roughly {k1(K(I, 1967, 'Births'))} from {k1(K(I, 1966, 'Births'))}", 'tl': f"sank to {F(tl, 'TFR'):.2f} in {tl}; it is {F(y, 'TFR'):.2f} now",
 'b50': f"below 1950's {m(P(I, 1950))} in {b50}", 'p2100': f"only {m(P(I, 2100))} remain", 'urb': f"peaked in 1992 at {p1(U[1992])}", 'median': f"The median age is {F(y, 'MedianAgePop'):.1f}",
 'ld': f"natural decrease in each year from {nn}",
}
sys.exit(run('romania', I, exp, ['population (millions)', 'ld'], yrs) > 0)
