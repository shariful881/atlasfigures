// Checks for the population ranking pages (task 21). Runs after `astro build` (part of `npm run check` and CI).
// The generated data (src/data/wpp/) is itself checked against the original UN files by check-site.mjs; this
// script checks that each ranking page, its JSON-LD and its CSV equal that data:
//   - every country or area in the UN file is in the table, in the right order, with the right value
//   - ItemList = the table (names, positions); FAQ in schema = FAQ on the page; JSON-LD numbers appear on the page
//   - CSV = the data (rank, iso3, values); Dataset points to the CSV and carries the UN licence
//   - Updated date = Article dateModified = sitemap lastmod; no full 7+ digit numbers in prose
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'node-html-parser';

const DIST = process.argv[2] || 'dist';
const BASE = '/atlasfigures';
const YEAR = 2026;
const problems = [];
let checks = 0;
const ok = (cond, where, what) => { checks++; if (!cond) problems.push(`${where}: ${what}`); return cond; };
const int = (v) => Math.round(v).toLocaleString('en-US');
const textOf = (el) => el.text.replace(/\s+/g, ' ').trim();

const index = JSON.parse(readFileSync('src/data/wpp/index.json', 'utf8')).countries;
const data = new Map(index.map((c) => [c.iso3, JSON.parse(readFileSync(join('src/data/wpp', c.file), 'utf8'))]));
const yr = (iso, y) => data.get(iso).years.find((r) => r.year === y);
const sitemap = readFileSync(join(DIST, 'sitemap.xml'), 'utf8');

const PAGES = {
  'population-by-country': { value: (iso) => yr(iso, YEAR).population, shown: (v) => int(v), csvCol: 5 },
  'population-density-by-country': { value: (iso) => yr(iso, YEAR).densityPerKm2, shown: (v) => int(v), csvCol: 5 },
};

for (const [slug, P] of Object.entries(PAGES)) {
  const url = `/rankings/${slug}/`, where = `page ${url}`;
  const file = join(DIST, 'rankings', slug, 'index.html');
  if (!ok(existsSync(file), where, 'page not built')) continue;
  const html = readFileSync(file, 'utf8');
  const root = parse(html);
  const meta = JSON.parse(readFileSync(`src/data/rankings/${slug}.json`, 'utf8'));

  // table = data
  const expected = [...data.keys()].sort((a, b) => P.value(b) - P.value(a));
  const trs = root.querySelectorAll('table.ranking tbody tr');
  ok(trs.length === expected.length && expected.length === index.length, where, `table has ${trs.length} rows, UN file has ${index.length}`);
  trs.forEach((tr, i) => {
    const iso = tr.getAttribute('data-iso3');
    ok(iso === expected[i], where, `row ${i + 1} is ${iso}, expected ${expected[i]}`);
    ok(Number(tr.getAttribute('data-rank')) === i + 1, where, `row ${i + 1} rank attribute ${tr.getAttribute('data-rank')}`);
    const val = textOf(tr.querySelector('.c-val .n'));
    if (ok(data.has(iso), where, `row ${i + 1}: ${iso} is not in the UN file`)) ok(val === P.shown(P.value(iso)), where, `${iso}: shown ${val}, data ${P.shown(P.value(iso))}`);
  });

  // JSON-LD
  const ld = root.querySelectorAll('script[type="application/ld+json"]').flatMap((s) => { const j = JSON.parse(s.text); return j['@graph'] ?? [j]; });
  const list = ld.find((n) => n['@type'] === 'ItemList');
  const art = ld.find((n) => n['@type'] === 'Article');
  const faq = ld.find((n) => n['@type'] === 'FAQPage');
  const ds = ld.find((n) => n['@type'] === 'Dataset');
  ok(list && art && faq && ds, where, 'needs Article + ItemList + Dataset + FAQPage');
  const names = trs.map((tr) => { const th = parse(tr.querySelector('.c-name').toString()); th.querySelector('.reg')?.remove(); return textOf(th); });
  ok(list?.numberOfItems === trs.length && list.itemListElement.every((e, i) => e.position === i + 1 && e.name === names[i]), where, 'ItemList differs from the table');
  const visible = parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, ''));
  const text = textOf(visible);
  for (const t of [art?.headline, art?.description, ...(faq?.mainEntity ?? []).flatMap((q) => [q.name, q.acceptedAnswer?.text])].filter(Boolean))
    for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
  ok(JSON.stringify(root.querySelectorAll('.faq details summary').map(textOf)) === JSON.stringify((faq?.mainEntity ?? []).map((q) => q.name)), where, 'FAQ in JSON-LD differs from the page');
  ok(ds?.license === 'https://creativecommons.org/licenses/by/3.0/igo/', where, 'Dataset licence is not CC BY 3.0 IGO');

  // CSV = data
  const csvUrl = ds?.distribution?.[0]?.contentUrl ?? '';
  const csvFile = join(DIST, csvUrl.replace(/^https?:\/\/[^/]+/, '').slice(BASE.length));
  if (ok(csvUrl.endsWith(`/data/${slug}.csv`) && existsSync(csvFile), where, `Dataset CSV ${csvUrl} missing`)) {
    const rows = readFileSync(csvFile, 'utf8').split('\n').filter((l) => /^\d+,/.test(l));
    ok(rows.length === expected.length, where, `CSV has ${rows.length} rows`);
    rows.forEach((l, i) => {
      const cells = l.match(/("([^"]|"")*"|[^,]*)(,|$)/g).map((c) => c.replace(/,$/, ''));
      const iso = cells[2];
      ok(Number(cells[0]) === i + 1 && iso === expected[i] && Number(cells[P.csvCol]) === P.value(iso), where, `CSV row ${i + 1} (${iso}) ≠ data`);
    });
  }

  // dates
  const upd = meta.updated;
  ok(art?.dateModified?.startsWith(upd), where, `Article dateModified ≠ Updated ${upd}`);
  ok(root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === upd), where, `Updated ${upd} not shown`);
  ok(new RegExp(`${BASE}${url}</loc><lastmod>${upd}</lastmod>`).test(sitemap), where, 'sitemap lastmod ≠ Updated (or page not in sitemap)');

  // prose style: no full numbers of 7+ digits in running text
  for (const p of visible.querySelectorAll('article .answer, article .prose p, article .faq p'))
    for (const m of textOf(p).match(/\d{1,3}(,\d{3}){2,}/g) ?? []) ok(false, where, `full number "${m}" in prose; write it as millions/billions`);
}

// ---------- World page (task 20) ----------
{
  const url = '/population/world/', where = `page ${url}`;
  const file = join(DIST, 'population', 'world', 'index.html');
  if (ok(existsSync(file), where, 'page not built')) {
    const html = readFileSync(file, 'utf8');
    const root = parse(html);
    const wd = JSON.parse(readFileSync('src/data/pages/world.json', 'utf8'));
    const world = JSON.parse(readFileSync('src/data/wpp/world.json', 'utf8'));
    const W = Object.fromEntries(world.years.map((r) => [r.year, r]));
    const now = W[YEAR];
    const visible = parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, ''));
    visible.querySelectorAll('nav.related-pages').forEach((el) => el.remove());
    const text = textOf(visible);
    const exp = { population: int(now.population), billions: `${(now.population / 1e9).toFixed(2)} billion`, growth: `${now.growthRatePct.toFixed(1)}%`, change: int(now.change),
      'births/day': int(Math.round(now.births / 365)), 'deaths/day': int(Math.round(now.deaths / 365)), density: int(now.densityPerKm2), median: now.medianAge.toFixed(1),
      fertility: now.fertility.toFixed(2), life: now.lifeExpectancy.toFixed(1), urban: `${now.urbanPct.toFixed(1)}%`, countries: String(index.length) };
    for (const [k, v] of Object.entries(exp)) ok(text.includes(v), where, `${k} ${v} (from the UN World data) is not on the page`);
    const live = root.querySelector('section.live');
    ok(live && Number(live.getAttribute('data-anchor')) === now.population && Number(live.getAttribute('data-rate')) === now.change && live.getAttribute('data-date') === `${YEAR}-07-01`, where, 'live counter anchor/rate/date ≠ UN World data');
    ok(live && textOf(live).includes('Estimate based on UN projections'), where, 'live counter label missing');
    for (const tr of root.querySelectorAll('table.data tbody tr')) {
      const cells = tr.querySelectorAll('th,td').map(textOf); const y = Number(cells[0].match(/\d{4}/)?.[0]);
      if (W[y]) ok(cells.some((t) => t.includes(int(W[y].population))), where, `table ${y}: population ≠ ${int(W[y].population)}`);
    }
    ok(root.querySelectorAll('table.data tbody tr:not(.band-label)').length === wd.tableYears.length, where, 'table rows ≠ tableYears');
    const ld = root.querySelectorAll('script[type="application/ld+json"]').flatMap((s) => { const j = JSON.parse(s.text); return j['@graph'] ?? [j]; });
    const art = ld.find((n) => n['@type'] === 'Article'), faq = ld.find((n) => n['@type'] === 'FAQPage'), ds = ld.find((n) => n['@type'] === 'Dataset');
    ok(art && faq && ds, where, 'needs Article + Dataset + FAQPage');
    for (const t of [art?.headline, art?.description, ...(faq?.mainEntity ?? []).flatMap((q) => [q.name, q.acceptedAnswer?.text])].filter(Boolean))
      for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
    ok(JSON.stringify(root.querySelectorAll('.faq details summary').map(textOf)) === JSON.stringify((faq?.mainEntity ?? []).map((q) => q.name)), where, 'FAQ in JSON-LD differs from the page');
    const csvFile = join(DIST, 'data', 'world-population.csv');
    if (ok(ds?.distribution?.[0]?.contentUrl?.endsWith('/data/world-population.csv') && existsSync(csvFile), where, 'Dataset CSV missing')) {
      const lines = readFileSync(csvFile, 'utf8').split('\n').filter((l) => /^\d{4},/.test(l));
      ok(lines.length === wd.tableYears.length, where, 'CSV rows ≠ tableYears');
      for (const l of lines) { const [y, pop] = l.split(','); ok(Number(pop) === W[Number(y)]?.population, where, `CSV ${y} ≠ UN data`); }
    }
    ok(art?.dateModified?.startsWith(wd.updated) && root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === wd.updated), where, 'Updated date ≠ dateModified / not shown');
    ok(new RegExp(`${BASE}${url}</loc><lastmod>${wd.updated}</lastmod>`).test(sitemap), where, 'sitemap lastmod ≠ Updated (or page not in sitemap)');
    for (const p of visible.querySelectorAll('article .answer, article .prose p, article .faq p'))
      for (const m of textOf(p).match(/\d{1,3}(,\d{3}){2,}/g) ?? []) ok(false, where, `full number "${m}" in prose`);
  }
  // Population hub: every country page listed once, plus the World card
  const hub = parse(readFileSync(join(DIST, 'population', 'index.html'), 'utf8'));
  const pages = readdirSync('src/data/countries').length;
  ok(hub.querySelectorAll('.list a.row').length === pages, 'page /population/', `hub lists ${hub.querySelectorAll('.list a.row').length} countries, ${pages} have pages`);
  ok(hub.querySelectorAll('a').some((a) => a.getAttribute('href') === `${BASE}/population/world/`), 'page /population/', 'hub does not link to the World page');
  ok(hub.querySelectorAll('.list a.row').every((a) => ['Asia', 'Africa', 'Europe', 'Americas', 'Oceania'].includes(a.getAttribute('data-continent'))), 'page /population/', 'a hub row has no valid continent for the filter');
}

if (problems.length) {
  console.log(`✗ Population rankings: ${problems.length} problem(s)`);
  for (const p of problems.slice(0, 40)) console.log('  - ' + p);
  process.exit(1);
}
console.log(`✓ Population rankings, World page and hub passed: ${checks} checks (table, order, values, ItemList, CSV, JSON-LD, FAQ, live counter, dates, style).`);
