// Downloadable CSV behind each country health page (task 160): every year with at least one value, every health
// series in HEALTH_COLS + HEALTH_CSV_EXTRA, values exactly as the World Bank publishes them (empty = no data).
import { econData, econMeta } from '../../lib/econ';
import { HEALTH_COLS, HEALTH_CSV_EXTRA } from '../../lib/topics';

const load = () =>
  Object.values(import.meta.glob('../../data/country-pages/*.json', { eager: true }) as Record<string, { default: any }>).map((m) => m.default).filter((c) => c.pages?.health);
const COLS = [...HEALTH_COLS, ...HEALTH_CSV_EXTRA];

export function getStaticPaths() {
  return load().map((c) => ({ params: { slug: c.slug } }));
}

export function GET({ params }: { params: { slug: string } }) {
  const c = load().find((x) => x.slug === params.slug)!;
  const s = econData(c.iso3).series as Record<string, [number, number][]>;
  const maps = COLS.map((k) => new Map(s[k.wdi]));
  const years = [...new Set(COLS.flatMap((k) => s[k.wdi].map(([y]) => y)))].sort((a, b) => a - b);
  const head = ['year', ...COLS.map((k) => k.csv)].join(',');
  const lines = years.map((y) => [y, ...maps.map((m) => (m.has(y) ? m.get(y) : ''))].join(','));
  const note = [
    `# ${c.name}, health. Source: ${econMeta.source} (${econMeta.sourceUrl}), WDI update ${econMeta.indicators.under5Mortality.wdiLastUpdated}. Licence: ${econMeta.licence}.`,
    `# Codes: ${COLS.map((k) => `${k.csv}=${econMeta.indicators[k.wdi].code}`).join('; ')}`,
    '# Values exactly as published by the World Bank; empty = no data. The World Bank does not endorse AtlasFigures.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': `inline; filename="${c.slug}-health.csv"` },
  });
}
