// Automatic checks for economy pages (/economy/<slug>/ and the /economy/ hub). Runs after `astro build`
// (part of `npm run check` and CI), next to check-site.mjs, which already checks every page for links,
// closed FAQ/Sources, "Report an error", ISO dates and noindex/sitemap rules.
//
// Per economy page: key World Bank figures from src/data/wdi/ (itself checked against the original files by
// check-wdi.mjs) are on the page in the site's money style; table cells = data; every number in the JSON-LD
// text is shown on the page; FAQ in schema = FAQ shown; Article + Dataset + FAQPage; Dataset licence CC BY 4.0;
// CSV = World Bank values exactly; Updated = dateModified = sitemap lastmod; number style in prose.
// Hub: lists every economy page, ItemList = list shown.
// Ranking pages: order, values, ItemList, CSV, flags (file exists) and world map (rank, shade order, legend).

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'node-html-parser';

const DIST = process.argv[2] || 'dist';
const BASE = '/atlasfigures';
const problems = [];
let checks = 0;
const ok = (cond, where, what) => { checks++; if (!cond) problems.push(`${where}: ${what}`); return cond; };
const textOf = (el) => el.text.replace(/\s+/g, ' ').trim();
const nodes = (root) => root.querySelectorAll('script[type="application/ld+json"]').flatMap((s) => { const d = JSON.parse(s.text); return d['@graph'] ?? [d]; });

// Money style, written independently of src/lib/econ.ts
const usd = (v) => (v >= 1e12 ? `$${(v / 1e12).toFixed(2)} trillion` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)} billion` : `$${(v / 1e6).toFixed(1)} million`);
const whole = (v) => `$${Math.round(v).toLocaleString('en-US')}`;
const pct = (v) => `${v.toFixed(1)}%`;
const last = (s) => s.at(-1);

const sitemap = existsSync(join(DIST, 'sitemap.xml')) ? readFileSync(join(DIST, 'sitemap.xml'), 'utf8') : '';
const lastmod = (u) => (sitemap.match(new RegExp(`<loc>[^<]*${BASE}${u.replace(/\//g, '\\/')}</loc><lastmod>([^<]+)</lastmod>`)) || [])[1];
const econ = existsSync('src/data/economy') ? readdirSync('src/data/economy').filter((f) => f.endsWith('.json')).map((f) => JSON.parse(readFileSync(join('src/data/economy', f), 'utf8'))) : [];

for (const c of econ) {
  const url = `/economy/${c.slug}/`;
  const where = `page ${url}`;
  const file = join(DIST, 'economy', c.slug, 'index.html');
  if (!ok(existsSync(file), where, 'page not built')) continue;
  const html = readFileSync(file, 'utf8');
  const root = parse(html);
  const visible = parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, ''));
  const text = textOf(visible);
  const s = JSON.parse(readFileSync(`src/data/wdi/countries/${c.iso3}.json`, 'utf8')).series;

  // key figures
  const exp = {
    GDP: usd(last(s.gdp)[1]), 'GDP per person': whole(last(s.gdpPerCapita)[1]), 'GDP growth': pct(last(s.gdpGrowthPct)[1]),
    inflation: pct(last(s.inflationPct)[1]), remittances: s.remittances.length ? usd(last(s.remittances)[1]) : null, 'remittances % of GDP': s.remittancesPctGdp.length ? pct(last(s.remittancesPctGdp)[1]) : null,
    unemployment: pct(last(s.unemploymentPct)[1]), 'internet users': pct(last(s.internetPct)[1]),
    'GDP per person, PPP': `Int$${Math.round(last(s.gdpPerCapitaPpp)[1]).toLocaleString('en-US')}`,
  };
  for (const [k, v] of Object.entries(exp)) if (v != null) ok(text.includes(v), where, `${k} ${v} (World Bank data) is not on the page`);
  ok(text.includes(String(last(s.gdp)[0])), where, 'latest World Bank year not shown');

  // table cells
  const m = (k) => new Map(s[k]);
  const G = m('gdp'), P = m('gdpPerCapita'), Gr = m('gdpGrowthPct'), I = m('inflationPct'), R = m('remittancesPctGdp');
  const rowsEl = root.querySelectorAll('table.econ tbody tr');
  ok(rowsEl.length === c.tableYears.length, where, `table has ${rowsEl.length} rows, tableYears ${c.tableYears.length}`);
  const cell = (map, y, f) => (map.has(y) ? f(map.get(y)) : '–');
  for (const tr of rowsEl) {
    const y = Number(tr.getAttribute('data-year'));
    const t = tr.querySelectorAll('td').map(textOf);
    const want = [cell(G, y, (v) => (v / 1e9).toFixed(1)), cell(P, y, whole), cell(Gr, y, (v) => `${Number(v.toFixed(1)) > 0 ? '+' : ''}${v.toFixed(1)}%`), cell(I, y, pct), cell(R, y, pct)];
    ok(JSON.stringify(t) === JSON.stringify(want), where, `table ${y}: ${JSON.stringify(t)} ≠ data ${JSON.stringify(want)}`);
  }

  // schema
  const n = nodes(root);
  const art = n.find((x) => x['@type'] === 'Article'), ds = n.find((x) => x['@type'] === 'Dataset'), fq = n.find((x) => x['@type'] === 'FAQPage');
  if (!ok(art && ds && fq, where, 'economy page needs Article + Dataset + FAQPage')) continue;
  for (const t of [art.headline, art.description, ds.name, ds.description, ...fq.mainEntity.flatMap((q) => [q.name, q.acceptedAnswer.text])]) {
    for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
  }
  const shownQ = root.querySelectorAll('.faq details summary').map(textOf);
  ok(JSON.stringify(shownQ) === JSON.stringify(fq.mainEntity.map((q) => q.name)), where, 'FAQ in JSON-LD differs from the page');
  ok(ds.license === 'https://creativecommons.org/licenses/by/4.0/', where, 'Dataset licence is not CC BY 4.0');
  ok(art.dateModified?.startsWith(c.updated) && ds.dateModified?.startsWith(c.updated), where, `dateModified ≠ Updated ${c.updated}`);
  ok(root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === c.updated), where, 'Updated date not shown');
  ok(lastmod(url) === c.updated, where, `sitemap lastmod ${lastmod(url)} ≠ Updated ${c.updated}`);
  ok(root.querySelector('details#sources') && /World Bank does not endorse/.test(textOf(root.querySelector('details#sources'))), where, 'Sources must say the World Bank does not endorse the page');

  // CSV = World Bank values exactly
  const csvUrl = ds.distribution?.[0]?.contentUrl ?? '';
  const csvPath = join(DIST, csvUrl.replace(/^https?:\/\/[^/]+/, '').slice(BASE.length));
  if (ok(csvUrl && existsSync(csvPath), where, `Dataset CSV ${csvUrl} missing`)) {
    const lines = readFileSync(csvPath, 'utf8').split('\n').filter((l) => l && !l.startsWith('#'));
    const head = lines[0].split(',');
    const keyOf = { gdp_current_usd: 'gdp', gdp_per_person_current_usd: 'gdpPerCapita', gdp_per_person_ppp_current_international_dollars: 'gdpPerCapitaPpp', gdp_growth_pct_constant_prices: 'gdpGrowthPct', inflation_consumer_prices_pct: 'inflationPct', unemployment_pct_modelled_ilo: 'unemploymentPct', remittances_received_current_usd: 'remittances', remittances_received_pct_gdp: 'remittancesPctGdp', internet_users_pct_population: 'internetPct' };
    ok(head.length === 10 && head.slice(1).every((h) => keyOf[h]), where, 'CSV header unexpected');
    let values = 0;
    for (const l of lines.slice(1)) {
      const f = l.split(','); const y = Number(f[0]);
      head.slice(1).forEach((h, i) => {
        const mp = new Map(s[keyOf[h]]); const cellV = f[i + 1];
        if (mp.has(y)) { values++; ok(Number(cellV) === mp.get(y), where, `CSV ${y} ${h} ≠ World Bank`); } else ok(cellV === '', where, `CSV ${y} ${h} has a value the World Bank does not`);
      });
    }
    const total = Object.values(keyOf).reduce((a, k) => a + s[k].length, 0);
    ok(values === total, where, `CSV holds ${values} values, World Bank ${total}`);
  }

  // number style in prose
  for (const el of visible.querySelectorAll('article .answer, article .prose p, article .faq p')) {
    const t = textOf(el); checks++;
    for (const x of t.match(/\d+\.\d{2,}%/g) ?? []) problems.push(`${where}: percent with more than 1 decimal in prose: "${x}"`);
    for (const x of t.match(/\b\d{1,3}(,\d{3}){2,}\b/g) ?? []) problems.push(`${where}: full number "${x}" in prose`);
    for (const x of t.matchAll(/\$(\d+(?:\.\d+)?) (billion|million)/g)) if (!/^\d+\.\d$/.test(x[1])) problems.push(`${where}: "${x[0]}" needs exactly 1 decimal`);
    for (const x of t.matchAll(/\$(\d+(?:\.\d+)?) trillion/g)) if (!/^\d+\.\d\d$/.test(x[1])) problems.push(`${where}: "${x[0]}" needs exactly 2 decimals`);
  }
}

// ranking pages
const RANKINGS = { 'gdp-by-country': { key: 'gdp', cell: (v) => (v / 1e9).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }), csvCol: 'gdp_current_usd' },
  'gdp-per-capita-by-country': { key: 'gdpPerCapita', cell: whole, csvCol: 'gdp_per_person_current_usd' },
  'inflation-rate-by-country': { key: 'inflationPct', cell: pct, csvCol: 'inflation_consumer_prices_pct' },
  'unemployment-rate-by-country': { key: 'unemploymentPct', cell: pct, csvCol: 'unemployment_pct_modelled_ilo' },
  'remittances-by-country': { key: 'remittances', cell: (v) => Math.round(v / 1e6).toLocaleString('en-US'), csvCol: 'remittances_received_current_usd' },
  'internet-users-by-country': { key: 'internetPct', cell: pct, csvCol: 'internet_users_pct_population', coverage: true },
  'mobile-subscriptions-by-country': { key: 'mobilePer100', cell: (v) => v.toFixed(1), csvCol: 'mobile_subscriptions_per_100_people', coverage: true },
  'child-mortality-by-country': { key: 'under5Mortality', cell: (v) => v.toFixed(1), csvCol: 'under5_mortality_per_1000_live_births' },
  'maternal-mortality-by-country': { key: 'maternalMortality', cell: (v) => v.toLocaleString('en-US'), csvCol: 'maternal_deaths_per_100000_live_births' },
  'exports-by-country': { key: 'exports', cell: (v) => (v / 1e9).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }), csvCol: 'exports_goods_services_current_usd', coverage: true },
  'imports-by-country': { key: 'imports', cell: (v) => (v / 1e9).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }), csvCol: 'imports_goods_services_current_usd', coverage: true },
  'land-area-by-country': { key: 'landArea', cell: (v) => v.toLocaleString('en-US', { maximumFractionDigits: 1 }), csvCol: 'land_area_sq_km' },
  'forest-area-by-country': { key: 'forestArea', cell: (v) => v.toLocaleString('en-US', { maximumFractionDigits: 1 }), csvCol: 'forest_area_sq_km' },
  // UNESCO education series are reported irregularly: each economy's latest value from `since` on (task 115).
  'literacy-rate-by-country': { key: 'literacyPct', cell: (v) => `${v.toFixed(1)}%`, csvCol: 'adult_literacy_pct_ages_15_plus', since: 2015 },
  'education-spending-by-country': { key: 'eduSpendPctGdp', cell: (v) => `${v.toFixed(1)}%`, csvCol: 'government_education_expenditure_pct_gdp', since: 2020 } };
const wdiAll = readdirSync('src/data/wdi/countries').map((f) => JSON.parse(readFileSync(join('src/data/wdi/countries', f), 'utf8')));
const wld = JSON.parse(readFileSync('src/data/wdi/aggregates.json', 'utf8')).aggregates.find((a) => a.code === 'WLD').series;
for (const [slug, R] of Object.entries(RANKINGS)) {
  const url = `/rankings/${slug}/`, where = `page ${url}`;
  const file = join(DIST, 'rankings', slug, 'index.html');
  if (!ok(existsSync(file), where, 'page not built')) continue;
  const html = readFileSync(file, 'utf8'); const root = parse(html);
  const text = textOf(parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, '')));
  const m = JSON.parse(readFileSync(`src/data/rankings/${slug}.json`, 'utf8'));
  // Year: World total's latest year, or for ITU telecom series the newest year with values for >= 80% of reporters.
  const cov = () => { const n = new Map(); for (const d of wdiAll) for (const [y] of d.series[R.key] ?? []) n.set(y, (n.get(y) ?? 0) + 1); const mx = Math.max(...n.values()); return Math.max(...[...n].filter(([, c]) => c >= 0.8 * mx).map(([y]) => y)); };
  const L = R.since ? null : R.coverage ? cov() : last(wld[R.key])[0];
  const latestFrom = (s) => { const k = (s ?? []).filter(([y]) => y >= R.since); return k.length ? k.at(-1) : null; };
  const want = R.since
    ? wdiAll.map((d) => { const l = latestFrom(d.series[R.key]); return { iso3: d.iso3, v: l?.[1], y: l?.[0] }; }).filter((x) => x.v != null).sort((a, b) => b.v - a.v || a.iso3.localeCompare(b.iso3))
    : wdiAll.map((d) => ({ iso3: d.iso3, v: new Map(d.series[R.key]).get(L), y: L })).filter((x) => x.v != null).sort((a, b) => b.v - a.v || a.iso3.localeCompare(b.iso3));
  const trs = root.querySelectorAll('table.ranking tbody tr');
  ok(trs.length === want.length, where, `ranking has ${trs.length} rows, World Bank ${want.length} economies with ${L} data`);
  trs.forEach((tr, i) => {
    const w = want[i]; if (!w) return;
    ok(tr.getAttribute('data-iso3') === w.iso3 && Number(tr.getAttribute('data-rank')) === i + 1, where, `row ${i + 1}: ${tr.getAttribute('data-iso3')} ≠ ${w.iso3}`);
    ok(textOf(tr.querySelector('td.c-val')) === R.cell(w.v), where, `row ${w.iso3}: value ${textOf(tr.querySelector('td.c-val'))} ≠ ${R.cell(w.v)}`);
  });
  // Flags (task 107): every row shows a flag file that exists in the build, or an empty placeholder.
  trs.forEach((tr) => {
    const img = tr.querySelector('th.c-name img.flag'), none = tr.querySelector('th.c-name .flag-none');
    if (!ok(img || none, where, `row ${tr.getAttribute('data-iso3')}: no flag`) || !img) return;
    const src = img.getAttribute('src') ?? '';
    ok(src.startsWith(BASE + '/') && existsSync(join(DIST, src.slice(BASE.length))) && img.getAttribute('alt') === '' && img.getAttribute('width') && img.getAttribute('height'), where, `row ${tr.getAttribute('data-iso3')}: flag file missing or img without alt=""/size`);
  });
  // Map (task 107): each shaded country/dot is a ranked economy, once, with its table rank; shades never get
  // lighter as values rise; legend counts add up to the ranking.
  const mapEl = root.querySelector('[data-worldmap]');
  if (ok(mapEl, where, 'ranking page has no world map')) {
    const swatches = mapEl.querySelectorAll('.map-legend .sw:not(.nd)').map((s) => (s.getAttribute('style') ?? '').replace('background:', '').trim());
    const items = mapEl.querySelectorAll('[data-iso3]');
    const rankOf = new Map(want.map((w, i) => [w.iso3, i + 1])), valOf = new Map(want.map((w) => [w.iso3, w.v]));
    const seen = new Set();
    for (const it of items) {
      const iso = it.getAttribute('data-iso3');
      ok(!seen.has(iso) && rankOf.get(iso) === Number(it.getAttribute('data-r')), where, `map ${iso}: duplicate or rank ≠ table`);
      seen.add(iso);
    }
    const shade = [...items].map((it) => ({ v: valOf.get(it.getAttribute('data-iso3')), c: swatches.indexOf(it.getAttribute('fill')) })).sort((a, b) => a.v - b.v);
    ok(shade.every((s, i) => s.c >= 0 && (i === 0 || s.c >= shade[i - 1].c)), where, 'map shades are not in value order');
    const counts = mapEl.querySelectorAll('.map-legend .ct').map((c) => Number(textOf(c).replace(/[()]/g, '')));
    ok(counts.reduce((a, b) => a + b, 0) === want.length && items.length >= want.length * 0.95, where, 'map legend counts ≠ ranking, or too few economies on the map');
  }
  const n = nodes(root);
  const art = n.find((x) => x['@type'] === 'Article'), il = n.find((x) => x['@type'] === 'ItemList'), ds = n.find((x) => x['@type'] === 'Dataset'), fq = n.find((x) => x['@type'] === 'FAQPage');
  if (!ok(art && il && ds && fq, where, 'ranking page needs Article + ItemList + Dataset + FAQPage')) continue;
  const names = trs.map((tr) => textOf(tr.querySelector('th.c-name')).replace(textOf(tr.querySelector('th.c-name .reg')), '').trim());
  ok(JSON.stringify(il.itemListElement.map((x) => x.name)) === JSON.stringify(names) && il.itemListElement.every((x, i) => x.position === i + 1), where, 'ItemList ≠ ranking shown');
  for (const t of [art.headline, art.description, ds.name, ds.description, ...fq.mainEntity.flatMap((q) => [q.name, q.acceptedAnswer.text])]) {
    for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
  }
  ok(JSON.stringify(root.querySelectorAll('.faq details summary').map(textOf)) === JSON.stringify(fq.mainEntity.map((q) => q.name)), where, 'FAQ in JSON-LD differs from the page');
  ok(ds.license === 'https://creativecommons.org/licenses/by/4.0/', where, 'Dataset licence is not CC BY 4.0');
  ok(art.dateModified?.startsWith(m.updated) && lastmod(url) === m.updated && root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === m.updated), where, 'Updated ≠ dateModified / sitemap / shown date');
  ok(/World Bank does not endorse/.test(textOf(root.querySelector('details#sources') ?? root)), where, 'Sources must say the World Bank does not endorse the page');
  const csvPath = join(DIST, (ds.distribution?.[0]?.contentUrl ?? '').replace(/^https?:\/\/[^/]+/, '').slice(BASE.length));
  if (ok(existsSync(csvPath), where, 'Dataset CSV missing')) {
    const lines = readFileSync(csvPath, 'utf8').split('\n').filter((l) => l && !l.startsWith('#'));
    const head = lines[0].split(','); const ci = head.indexOf(R.csvCol), ii = head.indexOf('iso3');
    ok(lines.length - 1 === want.length, where, 'CSV row count ≠ ranking');
    lines.slice(1).forEach((l, i) => {
      const f = l.match(/("([^"]|"")*"|[^,]*)(,|$)/g).map((x) => x.replace(/,$/, ''));
      ok(f[ii] === want[i]?.iso3 && Number(f[ci]) === want[i]?.v && Number(f[0]) === i + 1 && Number(f[head.indexOf('year')]) === want[i]?.y, where, `CSV row ${i + 1} ≠ World Bank`);
    });
  }
  for (const el of root.querySelectorAll('article .answer, article .prose p, article .faq p')) {
    const t = textOf(el); checks++;
    for (const x of t.match(/\d+\.\d{2,}%/g) ?? []) problems.push(`${where}: percent with more than 1 decimal in prose: "${x}"`);
    for (const x of t.matchAll(/\$(\d+(?:\.\d+)?) (billion|million)/g)) if (!/^\d+\.\d$/.test(x[1])) problems.push(`${where}: "${x[0]}" needs exactly 1 decimal`);
    for (const x of t.matchAll(/\$(\d+(?:\.\d+)?) trillion/g)) if (!/^\d+\.\d\d$/.test(x[1])) problems.push(`${where}: "${x[0]}" needs exactly 2 decimals`);
  }
}

// hub
{
  const file = join(DIST, 'economy', 'index.html');
  if (ok(existsSync(file), 'page /economy/', 'hub not built')) {
    const root = parse(readFileSync(file, 'utf8'));
    const links = root.querySelectorAll('#countries a.row').map((a) => a.getAttribute('href'));
    ok(links.length > 0, 'page /economy/', 'no #countries list');
    for (const c of econ) ok(links.includes(`${BASE}/economy/${c.slug}/`), 'page /economy/', `hub does not list ${c.slug}`);
    const list = nodes(root).find((x) => x['@type'] === 'CollectionPage')?.mainEntity?.itemListElement ?? [];
    ok(JSON.stringify(list.map((i) => i.url.replace(/^https?:\/\/[^/]+/, ''))) === JSON.stringify(links), 'page /economy/', 'ItemList ≠ list shown');
  }
}

if (problems.length) {
  console.log(`\n✗ Economy page check: ${problems.length} problem(s)\n`);
  for (const p of problems) console.log('  - ' + p);
  process.exit(1);
}
console.log(`✓ Economy pages passed: ${checks} checks on ${econ.length} country page(s), ${Object.keys(RANKINGS).length} ranking page(s) + hub (figures, tables, rankings, CSV, schema, dates, style).`);
