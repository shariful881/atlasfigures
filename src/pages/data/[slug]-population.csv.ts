// Downloadable CSV of the same yearly figures shown on each country page (its Dataset distribution).
// One file per country JSON in src/data/countries/; the years are that page's own table years.
import { countryData, displayRows } from '../../lib/figures';

const load = () =>
  Object.values(import.meta.glob('../../data/countries/*.json', { eager: true }) as Record<string, { default: any }>).map((m) => m.default);

export function getStaticPaths() {
  return load().map((c) => ({ params: { slug: c.slug } }));
}

export function GET({ params }: { params: { slug: string } }) {
  const c = load().find((x) => x.slug === params.slug)!;
  const un = countryData(c.iso3);
  const rows = displayRows(un.years, c.tableYears);
  const head = 'year,population,density_per_km2,births_per_woman,median_age,urban_pct_national_definition,net_migrants,world_rank,type';
  const lines = rows.map((r) => [r.year, r.population, r.density, r.fertility, r.medianAge, r.urbanPct ?? '', r.netMigrants, r.rank, r.projection ? 'UN projection' : 'UN estimate'].join(','));
  const note = [
    `# ${c.name}. Source: ${un.meta.source} Licence: ${un.meta.licence}.`,
    `# Urban share: ${un.meta.urban.source} Licence: ${un.meta.urban.licence}. Not projected after 2050.`,
    '# Compiled by AtlasFigures from the original UN data files.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': `inline; filename="${c.slug}-population.csv"` },
  });
}
