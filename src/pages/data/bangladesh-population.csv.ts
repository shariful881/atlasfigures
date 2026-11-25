// Downloadable CSV of the same yearly figures shown on /population/bangladesh/ (Dataset distribution).
import bd from '../../data/countries/bangladesh.json';
import { countryData, displayRows, CURRENT_YEAR } from '../../lib/figures';
export function GET() {
  const un = countryData(bd.iso3);
  const rows = displayRows(un.years, [1960, 1970, 1980, 1990, 2000, 2010, 2020, CURRENT_YEAR, 2030, 2040, 2050]);
  const head = 'year,population,density_per_km2,births_per_woman,median_age,urban_pct_national_definition,net_migrants,world_rank,type';
  const lines = rows.map((r) => [r.year, r.population, r.density, r.fertility, r.medianAge, r.urbanPct ?? '', r.netMigrants, r.rank, r.projection ? 'UN projection' : 'UN estimate'].join(','));
  const note = [
    `# Source: ${un.meta.source} Licence: ${un.meta.licence}.`,
    `# Urban share: ${un.meta.urban.source} Licence: ${un.meta.urban.licence}.`,
    '# Compiled by AtlasFigures from the original UN data files.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'inline; filename="bangladesh-population.csv"' },
  });
}
