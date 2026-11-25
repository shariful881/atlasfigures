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

if (problems.length) {
  console.log(`✗ Population rankings: ${problems.length} problem(s)`);
  for (const p of problems.slice(0, 40)) console.log('  - ' + p);
  process.exit(1);
}
console.log(`✓ Population rankings passed: ${checks} checks on ${Object.keys(PAGES).length} page(s) (table, order, values, ItemList, CSV, JSON-LD, FAQ, dates, style).`);
