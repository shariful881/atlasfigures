// CSV behind /population/world/ (its Dataset distribution): the same yearly World figures as the page table.
import wd from '../../data/pages/world.json';
import { worldData, displayRows } from '../../lib/figures';

export function GET() {
  const rows = displayRows(worldData.years, wd.tableYears);
  const head = 'year,population,density_per_km2,births_per_woman,median_age,urban_pct_national_definitions,type';
  const lines = rows.map((r) => [r.year, r.population, r.density, r.fertility, r.medianAge, r.urbanPct ?? '', r.projection ? 'UN projection' : 'UN estimate'].join(','));
  const note = [
    `# World. Source: ${worldData.meta.source} Licence: ${worldData.meta.licence}.`,
    `# Urban share: ${worldData.meta.urban.source} Licence: ${worldData.meta.urban.licence}. Not projected after 2050.`,
    '# Compiled by AtlasFigures from the original UN data files.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'inline; filename="world-population.csv"' },
  });
}
