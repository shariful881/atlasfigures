// Downloadable CSV of the World Bank figures behind each economy page (its Dataset distribution).
// One file per JSON in src/data/economy/; every year from 1960 with at least one value, values exactly as
// the World Bank publishes them (empty = no data).
import { econData, econMeta } from '../../lib/econ';

const load = () =>
  Object.values(import.meta.glob('../../data/economy/*.json', { eager: true }) as Record<string, { default: any }>).map((m) => m.default);

const COLUMNS: [string, string][] = [
  ['gdp', 'gdp_current_usd'],
  ['gdpPerCapita', 'gdp_per_person_current_usd'],
  ['gdpPerCapitaPpp', 'gdp_per_person_ppp_current_international_dollars'],
  ['gdpGrowthPct', 'gdp_growth_pct_constant_prices'],
  ['inflationPct', 'inflation_consumer_prices_pct'],
  ['unemploymentPct', 'unemployment_pct_modelled_ilo'],
  ['remittances', 'remittances_received_current_usd'],
  ['remittancesPctGdp', 'remittances_received_pct_gdp'],
  ['internetPct', 'internet_users_pct_population'],
];

export function getStaticPaths() {
  return load().map((c) => ({ params: { slug: c.slug } }));
}

export function GET({ params }: { params: { slug: string } }) {
  const c = load().find((x) => x.slug === params.slug)!;
  const s = econData(c.iso3).series as Record<string, [number, number][]>;
  const maps = COLUMNS.map(([k]) => new Map(s[k]));
  const years = [...new Set(COLUMNS.flatMap(([k]) => s[k].map(([y]) => y)))].sort((a, b) => a - b);
  const head = ['year', ...COLUMNS.map(([, h]) => h)].join(',');
  const lines = years.map((y) => [y, ...maps.map((m) => (m.has(y) ? m.get(y) : ''))].join(','));
  const note = [
    `# ${c.name}. Source: ${econMeta.source} (${econMeta.sourceUrl}), WDI update ${econMeta.indicators.gdp.wdiLastUpdated}. Licence: ${econMeta.licence}.`,
    '# Values exactly as published by the World Bank; empty = no data. The World Bank does not endorse AtlasFigures.',
    '# Compiled by AtlasFigures from the original World Bank data files.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': `inline; filename="${c.slug}-economy.csv"` },
  });
}
