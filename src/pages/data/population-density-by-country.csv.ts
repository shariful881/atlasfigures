// CSV behind /rankings/population-density-by-country/ (its Dataset distribution). UN WPP 2024 figures as generated
// from the original UN files; land area = population ÷ density (the area the UN uses).
import { byDensity } from '../../lib/popRankings';
import { worldData, CURRENT_YEAR } from '../../lib/figures';

export function GET() {
  const q = (v: unknown) => (typeof v === 'string' && /[",]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v ?? '');
  const head = 'rank,country_or_area,iso3,un_region,year,people_per_km2,population,land_area_km2,people_per_km2_2050_un_projection';
  const lines = byDensity().map((r) => [r.rank, q(r.name), r.iso3, q(r.region), CURRENT_YEAR, r.now.densityPerKm2, r.now.population, Math.round(r.landAreaKm2), r.yearOf(2050).densityPerKm2].join(','));
  const note = [
    `# population-density-by-country, ${CURRENT_YEAR}. Source: UN DESA Population Division, World Population Prospects 2024 (${worldData.meta.sourceUrl}), medium variant, with the interim update of 19 January 2026. Licence: CC BY 3.0 IGO.`,
    '# All countries and areas in the UN file. 2050 = UN medium-variant projection.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', { headers: { 'Content-Type': 'text/csv; charset=utf-8' } });
}
