# Run after `npm run build`: python3 scripts/verify/taiwan.py
# Independent check of every figure on /population/taiwan/ against the original UN files (UN listing: China, Taiwan Province of China).
import sys, json; sys.path.insert(0, "scripts/verify")
from _un import *
from _un import _rows
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
R = range(1950, 2101)
big = lambda y, mn, par=None: countries(y, mn, par) if par else countries(y, mn)
SR = lambda k, yr: f(k, yr, "TPopulationMale1July") / f(k, yr, "TPopulationFemale1July") * 100
I = 'NER'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/niger.json'))['tableYears']
ALL = countries(y)
I = 'TWN'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = json.load(open('src/data/countries/taiwan.json'))['tableYears']
ALL = countries(y); B = countries(y, 1e7); EAS = {'906'}
assert min(countries(2010), key=lambda k: f(k, 2010, 'TFR')) == I and all(F(yr, 'TFR') < 1 for yr in range(2020, y + 1))
assert sorted(ALL, key=lambda k: f(k, y, 'TFR'))[:5] == ['MAC', 'HKG', 'KOR', 'BLM', I]
pk = max(R, key=lambda yr: P(I, yr)); nn = next(yr for yr in R if K(I, yr, 'NatChange') < 0); assert pk == nn == 2019 and all(K(I, yr, 'NatChange') < 0 for yr in range(nn, 2101))
fall = lambda k: 1 - P(k, 2100) / P(k, y); assert sorted(B, key=lambda k: -fall(k))[:3] == ['UKR', 'KOR', I] and fall(I) > 0.5
assert sorted(B, key=lambda k: -f(k, y, 'PopDensity'))[:2] == ['BGD', I]
bt = max(range(1950, 2024), key=lambda yr: K(I, yr, 'Births')); assert bt == 1962
at = max(R, key=lambda yr: F(yr, 'MedianAgePop')); assert at == 2080
mf = next(yr for yr in range(1970, 2101) if SR(I, yr) < 100); assert mf == 2016 and all(SR(I, yr) < 100 for yr in range(mf, y + 1))
b20 = next(yr for yr in range(y, 2101) if P(I, yr) < 2e7); assert b20 == 2048
assert sorted(countries(y, 0, EAS), key=lambda k: -P(k, y)).index(I) == 4
exp = exp_base(I, y, U) | {
 'tfr 2010': f"The UN rate was {F(2010, 'TFR'):.2f} in 2010", 'births': f"near {k1(K(I, bt, 'Births'))} at their {bt} high, are down to about {k1(K(I, y, 'Births'))}",
 'peak': f"high point, {m(P(I, pk))}", 'deaths': f"about {k1(K(I, y, 'Deaths'))} deaths outweigh {k1(K(I, y, 'Births'))} births", 'change': f"declines by about {k1(-K(I, y, 'PopChange'))}",
 'b20': f"below 20 million in {b20}", 'pop 2100': f"{m(P(I, 2100))} remain in 2100", 'median 1990': f"up from {F(1990, 'MedianAgePop'):.1f} in 1990",
 'median top': f"peaks at {F(at, 'MedianAgePop'):.1f} in {at}", 'le': f"count on {F(y, 'LEx'):.1f} years", 'sr 1970': f"1970 ratio of {SR(I, 1970):.1f} males",
 'mf': f"each year from {mf}", 'ranks': f"ranked {ordn(rank(I, 1970))} in 1970, ranks {ordn(rank(I, y))} today and would be {ordn(rank(I, 2100))} by 2100",
 'density': f"{c(f(I, y, 'PopDensity'))} per square kilometre across {c(land(I))} km²",
}
sys.exit(run('taiwan', I, exp, ['population (millions)', 'tfr'], yrs) > 0)
