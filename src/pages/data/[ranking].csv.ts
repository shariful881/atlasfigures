// Downloadable CSVs behind the economy ranking pages (their Dataset distribution). Values exactly as the
// World Bank publishes them; rank = position among economies with a value for that year.
import { econData, econMeta, rankBy, rankingYear, valueIn } from '../../lib/econ';
import { commonName } from '../../lib/names';

const RANKINGS: Record<string, { key: 'gdp' | 'gdpPerCapita'; cols: [string, (iso3: string, y: number) => number | string | null][] }> = {
  'gdp-by-country': { key: 'gdp', cols: [
    ['gdp_current_usd', (x, y) => valueIn(econData(x).series.gdp, y)],
    ['gdp_growth_pct_constant_prices', (x, y) => valueIn(econData(x).series.gdpGrowthPct, y)],
    ['gdp_per_person_current_usd', (x, y) => valueIn(econData(x).series.gdpPerCapita, y)],
  ] },
  'gdp-per-capita-by-country': { key: 'gdpPerCapita', cols: [
    ['gdp_per_person_current_usd', (x, y) => valueIn(econData(x).series.gdpPerCapita, y)],
    ['gdp_per_person_ppp_current_international_dollars', (x, y) => valueIn(econData(x).series.gdpPerCapitaPpp, y)],
    ['world_bank_income_group', (x) => econData(x).incomeGroup],
  ] },
};

export function getStaticPaths() {
  return Object.keys(RANKINGS).map((ranking) => ({ params: { ranking } }));
}

export function GET({ params }: { params: { ranking: string } }) {
  const r = RANKINGS[params.ranking];
  const y = rankingYear(r.key);
  const q = (v: unknown) => (typeof v === 'string' && /[",]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v ?? '');
  const lines = rankBy(r.key, y).map((e) => [e.rank, q(commonName(e.iso3)), e.iso3, y, ...r.cols.map(([, f]) => q(f(e.iso3, y)))].join(','));
  const head = ['rank', 'country_or_area', 'iso3', 'year', ...r.cols.map(([h]) => h)].join(',');
  const note = [
    `# ${params.ranking}, ${y}. Source: ${econMeta.source} (${econMeta.sourceUrl}), WDI update ${econMeta.indicators.gdp.wdiLastUpdated}. Licence: ${econMeta.licence}.`,
    '# Values exactly as published by the World Bank; only economies with a value for this year are ranked. The World Bank does not endorse AtlasFigures.',
  ];
  return new Response([...note, head, ...lines].join('\n') + '\n', {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': `inline; filename="${params.ranking}.csv"` },
  });
}
