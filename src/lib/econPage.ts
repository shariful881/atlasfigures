// Shared plumbing for country economy pages (src/pages/economy/<slug>.astro): the figures behind the fixed UI
// (indicator cards, Key facts, yearly table) and the structured data. Only code is shared; every sentence,
// heading, FAQ, chart and table title is written on the page itself (no content templates).
import { econData, econMeta, aggregate, valueIn, latest, rankBy, usd, usdWhole, intDollars, signedPct, type IndicatorKey } from './econ';
import { pct, ord } from './figures';
import { abs, ORG_ID, WEBSITE_ID, PUBLISHER, longDate } from '../site';

export function econBasics(iso3: string, tableYears: number[]) {
  const e = econData(iso3);
  const s = e.series;
  const L = latest(s.gdp)!.year;
  const v = (k: IndicatorKey, y: number) => valueIn(s[k], y);
  const at = (k: IndicatorKey) => latest(s[k]);
  const gdp = v('gdp', L)!, perHead = v('gdpPerCapita', L)!, growth = v('gdpGrowthPct', L)!;
  const ppp = v('gdpPerCapitaPpp', L), unemp = v('unemploymentPct', L);
  const infl = at('inflationPct')!, rem = at('remittances'), remPct = at('remittancesPctGdp'), net = at('internetPct');
  const worldGdp = valueIn(aggregate('WLD').series.gdp, L)!;
  const share = (gdp / worldGdp) * 100;
  const gdpRank = rankBy('gdp', L).find((r) => r.iso3 === iso3)?.rank ?? null;
  const pcRank = rankBy('gdpPerCapita', L).find((r) => r.iso3 === iso3)?.rank ?? null;
  const yr = (y: number) => (y === L ? undefined : `${y}`);

  const cards = [
    { label: 'GDP', value: gdp >= 1e12 ? usd(gdp).replace(' trillion', 'T') : usd(gdp).replace(' billion', 'B'), year: L, note: 'current US$' },
    { label: 'GDP per person', value: usdWhole(perHead), year: L },
    { label: 'GDP growth', value: signedPct(growth), year: L },
    { label: 'Inflation', value: pct(infl.value), year: infl.year, note: 'consumer prices' },
  ];
  const factGroups = [
    { title: 'Size', facts: [
      { label: 'GDP', value: usd(gdp), note: `${L}, current US$` },
      ...(gdpRank ? [{ label: 'World rank by GDP', value: ord(gdpRank) }] : []),
      { label: 'Share of world GDP', value: pct(share) },
      { label: 'GDP growth', value: signedPct(growth), note: 'constant prices' },
    ] },
    { title: 'Income', facts: [
      { label: 'GDP per person', value: usdWhole(perHead), ...(pcRank ? { note: `${ord(pcRank)} in the world` } : {}) },
      ...(ppp != null ? [{ label: 'GDP per person, PPP', value: intDollars(ppp) }] : []),
      { label: 'World Bank income group', value: e.incomeGroup ?? '–' },
    ] },
    { title: 'Prices and jobs', facts: [
      { label: 'Inflation', value: pct(infl.value), note: `consumer prices${yr(infl.year) ? `, ${infl.year}` : ''}` },
      ...(unemp != null ? [{ label: 'Unemployment', value: pct(unemp), note: 'modelled ILO estimate' }] : []),
    ] },
    { title: 'Links abroad', facts: [
      ...(rem ? [{ label: 'Remittances received', value: usd(rem.value), ...(yr(rem.year) ? { note: `${rem.year}` } : {}) }] : []),
      ...(remPct ? [{ label: 'Remittances, share of GDP', value: pct(remPct.value) }] : []),
      ...(net ? [{ label: 'Internet users', value: pct(net.value), note: `${net.year}, share of people` }] : []),
    ] },
  ];
  const highlights = [
    { label: 'Share of world GDP', value: pct(share) },
    ...(gdpRank ? [{ label: 'World rank by GDP', value: ord(gdpRank) }] : []),
    ...(ppp != null ? [{ label: 'Per person, PPP', value: intDollars(ppp) }] : []),
    ...(unemp != null ? [{ label: 'Unemployment', value: pct(unemp) }] : []),
  ].slice(0, 4);
  const rows = tableYears.map((y) => ({
    year: y, gdp: v('gdp', y), gdpPerCapita: v('gdpPerCapita', y), growth: v('gdpGrowthPct', y),
    inflation: v('inflationPct', y), remittancesPctGdp: v('remittancesPctGdp', y),
  }));
  return { e, s, L, v, gdp, perHead, growth, ppp, unemp, infl, rem, remPct, net, share, gdpRank, pcRank, cards, factGroups, highlights, rows };
}

export interface EconSchemaInput {
  page: string; slug: string; name: string; wikipedia: string; L: number;
  headline: string; description: string; published: string; updated: string;
  faq: { q: string; a: string }[]; extraCitations?: { name: string; url: string; publisher?: string }[];
}
export function econSchema(x: EconSchemaInput) {
  const iso = (d: string) => `${d}T12:00:00+06:00`;
  return [
    {
      '@type': 'Article', '@id': abs(`${x.page}#article`), headline: x.headline, description: x.description,
      datePublished: iso(x.published), dateModified: iso(x.updated),
      author: { '@type': 'Organization', name: PUBLISHER, url: abs('/about/') }, publisher: { '@id': ORG_ID }, isPartOf: { '@id': WEBSITE_ID },
      mainEntityOfPage: abs(x.page), image: abs('/icon-512.png'), inLanguage: 'en',
      about: { '@type': 'Country', name: x.name, sameAs: x.wikipedia },
      citation: [
        { '@type': 'CreativeWork', name: 'World Development Indicators', url: econMeta.sourceUrl, publisher: { '@type': 'Organization', name: 'The World Bank' } },
        ...(x.extraCitations ?? []).map((c) => ({ '@type': 'CreativeWork', name: c.name, url: c.url, ...(c.publisher ? { publisher: { '@type': 'Organization', name: c.publisher } } : {}) })),
      ],
    },
    {
      '@type': 'Dataset', '@id': abs(`${x.page}#dataset`),
      name: `${x.name} GDP, GDP per person, growth, inflation, unemployment, remittances and internet use, 1960–${x.L}`,
      description: `Yearly World Bank World Development Indicators for ${x.name}, as published (WDI update of ${longDate(econMeta.indicators.gdp.wdiLastUpdated)}): GDP and GDP per person in current US$, GDP per person at purchasing power parity, real GDP growth, consumer price inflation, unemployment (modelled ILO estimate), personal remittances received and individuals using the internet.`,
      url: abs(x.page), creator: { '@id': ORG_ID }, isBasedOn: [econMeta.sourceUrl], temporalCoverage: `1960/${x.L}`,
      spatialCoverage: { '@type': 'Place', name: x.name },
      variableMeasured: Object.values(econMeta.indicators).map((i: any) => `${i.label} (${i.unit})`),
      dateModified: iso(x.updated), license: econMeta.licenceUrl,
      distribution: [{ '@type': 'DataDownload', encodingFormat: 'text/csv', contentUrl: abs(`/data/${x.slug}-economy.csv`) }],
    },
    { '@type': 'FAQPage', '@id': abs(`${x.page}#faq`), mainEntity: x.faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) },
  ];
}
