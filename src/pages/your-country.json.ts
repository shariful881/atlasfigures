// Data for the home page's "Your country" card (task 8): every country or area in the UN data with its 2026
// figures and links, plus the time zone -> country table. Fetched only after the visitor asks to see their country.
// Same figures as the ranking pages (byPopulation, from the original UN files); nothing typed by hand.
import tz from '../data/tz-country.json';
import { byPopulation } from '../lib/popRankings';
import { pagesOf, iso2 } from '../lib/names';
import { path } from '../site';
import { CURRENT_YEAR } from '../lib/figures';

const flags = import.meta.glob('/node_modules/flag-icons/flags/4x3/*.svg', { eager: true, query: '?url&no-inline', import: 'default' }) as Record<string, string>;
const flagUrl = (code: string | null) => (code ? Object.entries(flags).find(([p]) => p.endsWith(`/${code}.svg`))?.[1] ?? null : null);

export function GET() {
  const list = byPopulation();
  const countries = list.map((e) => {
    const pg = pagesOf(e.iso3);
    const c = iso2(e.iso3);
    return {
      i: e.iso3, c, n: e.name, f: flagUrl(c),
      p: e.now.population, ch: e.now.change, r: e.rank, g: e.now.growthRatePct, d: e.now.densityPerKm2, a: e.now.medianAge,
      u: pg.population ? path(pg.population) : null, e: pg.economy ? path(pg.economy) : null,
    };
  });
  return new Response(JSON.stringify({ year: CURRENT_YEAR, total: list.length, ranking: path('/rankings/population-by-country/'), countries, zones: (tz as any).zones }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
