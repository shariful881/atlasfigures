---
// Ranking page scaffolded by scripts/tools/new-ranking.mjs (task 149). Structure, data, schema, CSV, FAQ and
// Sources are wired; EVERYTHING marked WRITE is this page's own text and must be written by hand
// (no two pages share wording). The build fails until the guard below is removed.
import Base from '../../layouts/Base.astro';
import LineChart from '../../components/LineChart.astro';
import RankingTable from '../../components/RankingTable.astro';
import WorldMap from '../../components/WorldMap.astro';
import IndicatorCards from '../../components/IndicatorCards.astro';
import SourceBadge from '../../components/SourceBadge.astro';
import PageTabs from '../../components/PageTabs.astro';
import meta from '../../data/rankings/{{SLUG}}.json';
import { econData, econMeta, aggregate, valueIn, {{RANKFN}}, rankingYear } from '../../lib/econ';
import { assertClaim, ord, int, pct } from '../../lib/figures';
import { highestSince, lowestSince, streak, aboveSince, belowSince, times } from '../../lib/claims';
import { commonName, pagesOf } from '../../lib/names';
import { abs, path, longDate, ORG_ID, WEBSITE_ID, PUBLISHER, reportErrorUrl } from '../../site';

assertClaim(false, 'WRITE: {{SLUG}} is a scaffold — write the text, pick the facts (find-facts), then delete this line');

const PAGE = '/rankings/{{SLUG}}/';
const PUBLISHED = meta.published, UPDATED = meta.updated;
const iso = (d: string) => `${d}T12:00:00+06:00`;
const WDI = 'World Bank, World Development Indicators';
const WDI_URL = econMeta.sourceUrl;
const checkedOn = meta.verification?.checkedOn;
const name = commonName;
const M = econMeta.indicators.{{KEY}};
const fmt = {{FMT}};

{{RANKSETUP}}
const N = ranked.length;
const wV = valueIn(aggregate('WLD').series.{{KEY}}, L);
const byIso = (x: string) => ranked.find((r) => r.iso3 === x);

// WRITE: the facts this page's sentences rely on, each with an assertClaim (see find-facts output).

const title = `WRITE title with ${L} | AtlasFigures`;           // ≤ ~60 characters, own wording
const description = `WRITE: one or two sentences answering the main question with real figures.`;

const cards = [
  ...(wV != null ? [{ label: 'World', value: fmt(wV), year: L, note: 'WRITE' }] : []),
  { label: `Highest: ${name(ranked[0].iso3)}`, value: fmt(ranked[0].value), year: L, note: 'WRITE' },
];
const top = ranked[0].value || 1;
const rows = ranked.map((r) => {
  const pg = pagesOf(r.iso3); const site = pg.population ?? pg.economy;
  return { rank: r.rank, iso3: r.iso3, name: name(r.iso3), site, href: site ? path(site) : null, region: r.region, bar: Math.max(0, r.value) / top, value: fmt(r.value), cells: [] };
});
const mapRows = ranked.map((r) => ({ iso3: r.iso3, name: name(r.iso3), rank: r.rank, raw: r.value, value: fmt(r.value) }));
const regions = [...new Set(ranked.map((r) => r.region))].sort();

const faq = [
  { q: 'WRITE: a real search question', a: `WRITE` },
];

const schema = [
  {
    '@type': 'Article', '@id': abs(`${PAGE}#article`), headline: `WRITE headline, ${L}`, description,
    datePublished: iso(PUBLISHED), dateModified: iso(UPDATED),
    author: { '@type': 'Organization', name: PUBLISHER, url: abs('/about/') }, publisher: { '@id': ORG_ID }, isPartOf: { '@id': WEBSITE_ID },
    mainEntityOfPage: abs(PAGE), image: abs('/icon-512.png'), inLanguage: 'en',
    citation: [{ '@type': 'CreativeWork', name: 'World Development Indicators', url: WDI_URL, publisher: { '@type': 'Organization', name: 'The World Bank' } }],
  },
  {
    '@type': 'ItemList', '@id': abs(`${PAGE}#ranking`), name: `WRITE list name, ${L}`, itemListOrder: 'https://schema.org/ItemListOrderDescending', numberOfItems: N,
    itemListElement: rows.map((r) => ({ '@type': 'ListItem', position: r.rank, name: r.name, ...(r.site ? { url: abs(r.site) } : {}) })),
  },
  {
    '@type': 'Dataset', '@id': abs(`${PAGE}#dataset`), name: `WRITE dataset name, ${L}`,
    description: `WRITE: what the CSV holds for ${N} countries and areas (WDI update of ${longDate(M.wdiLastUpdated)}).`,
    url: abs(PAGE), creator: { '@id': ORG_ID }, isBasedOn: [WDI_URL], temporalCoverage: `${L}`,
    spatialCoverage: { '@type': 'Place', name: 'World' }, variableMeasured: [M.wbName],
    dateModified: iso(UPDATED), license: econMeta.licenceUrl,
    distribution: [{ '@type': 'DataDownload', encodingFormat: 'text/csv', contentUrl: abs('/data/{{SLUG}}.csv') }],
  },
  { '@type': 'FAQPage', '@id': abs(`${PAGE}#faq`), mainEntity: faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) },
];
---
<Base
  title={title} description={description} section="rankings" appTitle="{{SHORT}}" back="/rankings/" ogType="article"
  breadcrumbs={[{ name: 'Home', href: '/' }, { name: 'Rankings', href: '/rankings/' }, { name: '{{TITLE}}', href: PAGE }]}
  schema={schema}
>
  <article class="country-main rank-page">
    <h1>WRITE H1 ({L})</h1>
    <p class="answer">WRITE: the direct answer in one or two sentences.</p>
    <div class="dates"><span>Updated <time datetime={UPDATED}>{longDate(UPDATED)}</time></span><SourceBadge source={WDI} url={WDI_URL} checkedOn={checkedOn} /></div>
    <IndicatorCards label={`{{TITLE}}, ${L}`} cards={cards} />

    <div class="segments" role="tablist" aria-label="Page sections">
      <button role="tab" aria-selected="true" data-panel="data">Ranking</button>
      <button role="tab" aria-selected="false" data-panel="map">Map</button>
      <button role="tab" aria-selected="false" data-panel="story">Story</button>
      <button role="tab" aria-selected="false" data-panel="faq">FAQ</button>
    </div>

    <section class="panel" data-panel="map" aria-label="Map" hidden-mobile>
      <WorldMap id="map-h" title={`WRITE map title, ${L}`} subtitle="WRITE map subtitle." rows={mapRows} fmt={fmt} source={WDI} sourceUrl={WDI_URL} checkedOn={checkedOn} />
    </section>
    <section class="panel" data-panel="data" aria-label="Ranking">
      <RankingTable
        id="rank-h" title={`WRITE table title, ${L}`} subtitle="WRITE table subtitle." valueLabel="{{VALUELABEL}}"
        cols={[]} rows={rows} regions={regions}
        source={WDI} sourceUrl={WDI_URL} checkedOn={checkedOn}
        csv={path('/data/{{SLUG}}.csv')} csvName="{{SLUG}}.csv"
        licence={{ name: 'CC BY 4.0 (World Bank data)', url: econMeta.licenceUrl }}
      />
      <p class="note">WRITE: who is ranked and who is missing ({N} countries and areas).</p>
    </section>

    <section class="panel" data-panel="story" aria-label="The story">
      <div class="story-block prose">
        <h2>WRITE: a question people search, answered in the first sentence</h2>
        <p>WRITE</p>
      </div>
    </section>

    <section class="panel" data-panel="faq" aria-labelledby="faq-h">
      <h2 id="faq-h">WRITE FAQ heading</h2>
      <div class="faq">{faq.map((f) => (<details><summary><h3>{f.q}</h3></summary><p>{f.a}</p></details>))}</div>
    </section>

    <details class="sources-details" id="sources">
      <summary><h2>Sources and methodology</h2></summary>
      <div class="sources-block">
        <ul class="sources">
          <li><a href={WDI_URL}>World Bank, World Development Indicators</a> (original bulk files, WDI update of {longDate(M.wdiLastUpdated)}): {M.wbName} ({{CODE}}). Licence CC BY 4.0. The World Bank does not endorse this page.</li>
        </ul>
        <p class="note">WRITE: definition and caveats from the indicator notes. See our <a href={path('/methodology/')}>methodology</a>.</p>
        <p class="note">Published <time datetime={PUBLISHED}>{longDate(PUBLISHED)}</time> · Updated <time datetime={UPDATED}>{longDate(UPDATED)}</time> · By {PUBLISHER}</p>
        <p class="note report-error">Spotted an error? <a href={reportErrorUrl('{{TITLE}}', PAGE)}>Report an error</a> · <a href={path('/corrections/')}>How we correct errors</a></p>
      </div>
    </details>
  </article>
  <PageTabs />
</Base>
<style>
  .rank-page { max-width: 980px; }
  .rank-page .note { margin: 4px 2px 20px; }
</style>
