// Downloadable CSVs behind the economy ranking pages (their Dataset distribution). Values exactly as the
// World Bank publishes them; rank = position among economies with a value for that year.
import { econData, econMeta, rankBy, rankingYear, coverageYear, valueIn } from '../../lib/econ';
import { commonName } from '../../lib/names';

const RANKINGS: Record<string, { key: 'gdp' | 'gdpPerCapita' | 'inflationPct' | 'unemploymentPct' | 'remittances' | 'internetPct' | 'mobilePer100' | 'under5Mortality' | 'maternalMortality'; coverage?: boolean; cols: [string, (iso3: string, y: number) => number | string | null][] }> = {
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
  'inflation-rate-by-country': { key: 'inflationPct', cols: [
    ['inflation_consumer_prices_pct', (x, y) => valueIn(econData(x).series.inflationPct, y)],
    ['inflation_previous_year_pct', (x, y) => valueIn(econData(x).series.inflationPct, y - 1)],
    ['world_bank_income_group', (x) => econData(x).incomeGroup],
  ] },
  'unemployment-rate-by-country': { key: 'unemploymentPct', cols: [
    ['unemployment_pct_modelled_ilo', (x, y) => valueIn(econData(x).series.unemploymentPct, y)],
    ['unemployment_2020_pct', (x) => valueIn(econData(x).series.unemploymentPct, 2020)],
    ['world_bank_income_group', (x) => econData(x).incomeGroup],
  ] },
  'internet-users-by-country': { key: 'internetPct', coverage: true, cols: [
    ['internet_users_pct_population', (x, y) => valueIn(econData(x).series.internetPct, y)],
    ['internet_users_2015_pct', (x) => valueIn(econData(x).series.internetPct, 2015)],
    ['world_bank_income_group', (x) => econData(x).incomeGroup],
  ] },
  'mobile-subscriptions-by-country': { key: 'mobilePer100', coverage: true, cols: [
    ['mobile_subscriptions_per_100_people', (x, y) => valueIn(econData(x).series.mobilePer100, y)],
    ['mobile_subscriptions', (x, y) => valueIn(econData(x).series.mobileSubs, y)],
    ['fixed_broadband_per_100_people', (x, y) => valueIn(econData(x).series.broadbandPer100, y)],
  ] },
  'child-mortality-by-country': { key: 'under5Mortality', cols: [
    ['under5_mortality_per_1000_live_births', (x, y) => valueIn(econData(x).series.under5Mortality, y)],
    ['infant_mortality_per_1000_live_births', (x, y) => valueIn(econData(x).series.infantMortality, y)],
    ['under5_mortality_1990_per_1000', (x) => valueIn(econData(x).series.under5Mortality, 1990)],
  ] },
  'maternal-mortality-by-country': { key: 'maternalMortality', cols: [
    ['maternal_deaths_per_100000_live_births', (x, y) => valueIn(econData(x).series.maternalMortality, y)],
    ['maternal_deaths_2000_per_100000', (x) => valueIn(econData(x).series.maternalMortality, 2000)],
    ['world_bank_income_group', (x) => econData(x).incomeGroup],
  ] },
  'remittances-by-country': { key: 'remittances', cols: [
    ['remittances_received_current_usd', (x, y) => valueIn(econData(x).series.remittances, y)],
    ['remittances_received_pct_gdp', (x, y) => valueIn(econData(x).series.remittancesPctGdp, y)],
  ] },
};

export function getStaticPaths() {
  return Object.keys(RANKINGS).map((ranking) => ({ params: { ranking } }));
}

export function GET({ params }: { params: { ranking: string } }) {
  const r = RANKINGS[params.ranking];
  const y = r.coverage ? coverageYear(r.key) : rankingYear(r.key);
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
