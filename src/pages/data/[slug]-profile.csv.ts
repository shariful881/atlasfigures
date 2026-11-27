// Downloadable CSV behind each country hub (/country/<slug>/, task 160): one row per live statistic in the
// country profile — section, statistic, value (as the source publishes it), unit, year, world rank and source.
// Same rows as the hub's "All figures" tables (single-source facts only after a hand check).
import { profile, liveStats } from '../../lib/profile';

const load = () =>
  Object.values(import.meta.glob('../../data/country-pages/*.json', { eager: true }) as Record<string, { default: any }>).map((m) => m.default).filter((c) => c.pages?.hub);

const q = (v: unknown) => { const s = v == null ? '' : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };

export function getStaticPaths() {
  return load().map((c) => ({ params: { slug: c.slug } }));
}

export function GET({ params }: { params: { slug: string } }) {
  const c = load().find((x) => x.slug === params.slug)!;
  const p = profile(c.iso3);
  const head = 'section,statistic,value,text,unit,year,un_projection,world_rank,ranked_countries,rank_order,source';
  const lines = p.sections.flatMap((s) => liveStats(p, s.id, c.checkedFacts).map((x) =>
    [s.label, x.label, x.value, x.text, x.unit, x.year, x.projection ? 'yes' : '', x.rank, x.of, x.rank ? (x.rankBy === 'low' ? 'lowest first' : 'highest first') : '', x.source].map(q).join(',')));
  const note = [
    `# ${c.name}: every statistic on https://atlasfigures.com/country/${c.slug}/ with its latest year. Compiled by AtlasFigures.`,
    '# Sources per row: UN World Population Prospects 2024 (CC BY 3.0 IGO; 2026 values are UN projections), World Bank World Development Indicators (CC BY 4.0; the World Bank does not endorse AtlasFigures), Global Carbon Project and Ember (CC BY 4.0), Unicode CLDR, GeoNames (CC BY 4.0), IANA tz, Wikidata (CC0).',
    '# world_rank = our calculation among countries or areas with a value in the five years before the year shown.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': `inline; filename="${c.slug}-profile.csv"` },
  });
}
