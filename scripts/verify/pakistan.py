# Run after `npm run build`: python3 scripts/verify/pakistan.py
# Independent check of every figure on /country/pakistan/population/ against the original UN files.
import sys; sys.path.insert(0, 'scripts/verify')
from _un import *
I = 'PAK'; y = 2026; U = urban(I); F = lambda yr, col: f(I, yr, col)
ch = K(I, y, 'PopChange'); yrs = [1950,1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050,2075,2100]
pass_idn = next(yr for yr in range(1950, 2101) if P(I, yr) > P('IDN', yr)); pass_usa = next(yr for yr in range(1950, 2101) if P(I, yr) > P('USA', yr))
tmax = max(range(1950, 2101), key=lambda yr: F(yr, 'TFR')); sub = next(yr for yr in range(1950, 2101) if F(yr, 'TFR') < 2.1)
opeak = min(range(1950, 2024), key=lambda yr: F(yr, 'NetMigrations'))
osince = next(s for s in range(1950, 2024) if all(F(k, 'NetMigrations') < 0 for k in range(s, 2024)))
exp = {
 'population (full)': c(P(I, y)), 'population (millions)': m(P(I, y)), 'rank': ordn(rank(I, y)), 'share': p1(P(I, y) / P('WORLD', y) * 100),
 'growth': p1(F(y, 'PopGrowthRate')), 'change (full)': c(ch), 'change (millions)': m(ch), 'per day (100s)': c(round(ch / 365 / 100) * 100),
 'density': c(F(y, 'PopDensity')), 'land': c(land(I)) + ' km²', 'pass IDN': str(pass_idn), 'pass USA': str(pass_usa), 'pop 1950': m(P(I, 1950)),
 'times': f"{P(I, y)/P(I, 1950):.1f} times", 'pop 2050': m(P(I, 2050)), 'pop 2100': m(P(I, 2100)), 'tfr': f"{F(y,'TFR'):.2f}", 'tfr max': f"{F(tmax,'TFR'):.2f}",
 'tfr max year': str(tmax), 'below 2.1 from': str(sub), 'births': m(K(I, y, 'Births')), 'births/day': c(round(K(I, y, 'Births') / 365 / 1000) * 1000),
 'median': f"{F(y,'MedianAgePop'):.1f}", 'median 1950': f"{F(1950,'MedianAgePop'):.1f}", 'median 2050': f"{F(2050,'MedianAgePop'):.1f}",
 'out since': str(osince), 'out peak year': str(opeak), 'out peak': m(-K(I, opeak, 'NetMigrations')), 'net emigration': m(-K(I, y, 'NetMigrations')),
 'natural': m(K(I, y, 'NatChange')), 'IMR': f"{F(y,'IMR'):.1f}", 'IMR 1950': str(round(F(1950, 'IMR'))), 'LE 1950': f"{F(1950,'LEx'):.1f}", 'LE': f"{F(y,'LEx'):.1f}",
 'urban': p1(U[y]), 'urban 1950': p1(U[1950]), 'urban 2050': p1(U[2050]), 'growth 2050': p1(F(2050, 'PopGrowthRate')),
}
sys.exit(run('pakistan', I, exp, ['population (millions)', 'change (millions)', 'pass USA', 'pass IDN', 'growth', 'growth 2050', 'pop 2050', 'pop 2100', 'urban', 'urban 2050'], yrs) > 0)
