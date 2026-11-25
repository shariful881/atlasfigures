// Downloadable CSV of the same yearly figures shown on /population/bangladesh/ (Dataset distribution).
import bd from '../../data/countries/bangladesh.json';
export function GET() {
  const head = 'year,population,density_per_km2,births_per_woman,median_age,urban_pct,net_migrants,world_rank,type';
  const rows = bd.series.map((r: any) =>
    [r.year, r.population, r.density, r.fertility, r.medianAge, r.urbanPct, r.netMigrants, r.rank, r.projection ? 'UN projection' : 'estimate'].join(','),
  );
  const note = `# Source: ${bd.source}. Compiled by AtlasFigures.`;
  return new Response([note, head, ...rows].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'inline; filename="bangladesh-population.csv"' },
  });
}
