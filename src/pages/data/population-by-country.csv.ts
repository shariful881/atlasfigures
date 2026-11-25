// CSV behind /rankings/population-by-country/ (its Dataset distribution). UN WPP 2024 figures as generated from the
// original UN files; rank = position among all countries or areas in the UN file for the year.
import { byPopulation } from '../../lib/popRankings';
import { worldData, CURRENT_YEAR } from '../../lib/figures';

export function GET() {
  const q = (v: unknown) => (typeof v === 'string' && /[",]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v ?? '');
  const head = 'rank,country_or_area,iso3,un_region,year,population,share_of_world_pct,growth_rate_pct,people_per_km2,population_2050_un_projection';
  const lines = byPopulation().map((r) => [r.rank, q(r.name), r.iso3, q(r.region), CURRENT_YEAR, r.now.population, r.now.worldSharePct, r.now.growthRatePct, r.now.densityPerKm2, r.yearOf(2050).population].join(','));
  const note = [
    `# population-by-country, ${CURRENT_YEAR}. Source: UN DESA Population Division, World Population Prospects 2024 (${worldData.meta.sourceUrl}), medium variant, with the interim update of 19 January 2026. Licence: CC BY 3.0 IGO.`,
    '# All countries and areas in the UN file. 2050 = UN medium-variant projection.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', { headers: { 'Content-Type': 'text/csv; charset=utf-8' } });
}
