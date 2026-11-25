# Run after `npm run build`: python3 scripts/verify/dr-congo.py
# Independent check of every figure on /population/dr-congo/ against the original UN files.
import sys; sys.path.insert(0, "scripts/verify")
from _un import *
exp_base = lambda I, y, U: {"population (full)": c(P(I, y)), "population (millions)": m(P(I, y)), "rank": ordn(rank(I, y)), "share": p1(P(I, y) / P("WORLD", y) * 100), "growth": p1(f(I, y, "PopGrowthRate")), "growth (+)": "+" + p1(f(I, y, "PopGrowthRate")), "change (full)": c(K(I, y, "PopChange")), "per day": c(K(I, y, "PopChange") / 365), "density": c(f(I, y, "PopDensity")), "land": c(land(I)) + " km²", "urban": p1(U[y]), "median": f"{f(I, y, 'MedianAgePop'):.1f}", "tfr": f"{f(I, y, 'TFR'):.2f}", "LE": f"{f(I, y, 'LEx'):.1f}"}
I = 'COD'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
B = countries(y, 10e6)
assert sorted(B, key=lambda k: -f(k, y, 'PopGrowthRate')).index(I) < 3 and F(y, 'PopGrowthRate') > 3
assert sorted(B, key=lambda k: f(k, y, 'MedianAgePop')).index(I) < 5
gain = sorted(countries(y), key=lambda k: -(P(k, 2100) - P(k, y))); assert gain[0] == I and P(I, 2100) - P(I, y) > 310e6
pe = next(yr for yr in range(2027, 2101) if P(I, yr) > P('ETH', yr)); pu = next(yr for yr in range(2027, 2101) if P(I, yr) > P('USA', yr)); assert (pe, pu) == (2056, 2097) and rank(I, 2100) == 5 and rank(I, 2050) == 8
dbl = next(yr for yr in range(1950, 2101) if P(I, yr) >= 2 * P(I, y)); p400 = next(yr for yr in range(1950, 2101) if P(I, yr) >= 400e6); assert 2090 <= p400 < 2100
assert sorted(countries(y), key=lambda k: -K(k, y, 'PopChange'))[:4] == ['IND', 'NGA', 'PAK', I]
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); assert tmax == 2000 and all(F(yr, 'TFR') >= 2.1 for yr in range(1950, 2101)) and F(2050, 'TFR') > 3
AF = countries(y, 0, AFRICA); assert sorted(AF, key=lambda k: -P(k, y)).index(I) == 3 and sorted(countries(y, 0, {'911'}), key=lambda k: -P(k, y))[0] == I
exp = exp_base(I, y, U) | {
 'gain to 2100': m(P(I, 2100) - P(I, y)), 'pop 2100': m(P(I, 2100)), 'pass ETH': f"({pe})", 'pass USA': f"({pu})", 'tfr max': f"{F(tmax,'TFR'):.2f} peak of {tmax}",
 'births': m(K(I, y, 'Births')), 'deaths': k1(K(I, y, 'Deaths')), 'median 2050': f"{F(2050,'MedianAgePop'):.1f}", 'median 2100': f"{F(2100,'MedianAgePop'):.1f}",
 'pop 2050': m(P(I, 2050)), 'rank 2050': ordn(rank(I, 2050)), 'double': f"by {dbl}", 'pop 1950': m(P(I, 1950)), 'rank 2100': ordn(rank(I, 2100)),
}
sys.exit(run('dr-congo', I, exp, ['population (millions)', 'median', 'pop 2100', 'pop 2050'], yrs) > 0)
