// Automatic checks for the energy and CO2 data and pages (task 110). Runs after `astro build` (part of
// `npm run check` and CI). Two parts:
//  1. Generated data = original files: every value in src/data/energy/index.json is compared with the original
//     Global Carbon Project and Ember files in data/raw/energy/ (parsed here independently of build-energy.mjs),
//     and every original value for a UN-listed country or area is present.
//  2. Ranking pages (/rankings/co2-emissions-by-country/, /rankings/renewable-electricity-by-country/): order and
//     values of every row = original files; flags; world map; ItemList = rows; every JSON-LD number is on the
//     page; FAQ in schema = FAQ shown; Dataset licence CC BY 4.0; CSV = original values; Updated = dateModified =
//     sitemap lastmod; number style in prose. check-site.mjs covers links, closed FAQ/Sources and "Report an error".
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'node-html-parser';

const DIST = process.argv[2] || 'dist';
const BASE = '/atlasfigures';
const RAW = 'data/raw/energy';
const problems = [];
let checks = 0;
const ok = (cond, where, what) => { checks++; if (!cond) problems.push(`${where}: ${what}`); return cond; };
const textOf = (el) => el.text.replace(/\s+/g, ' ').trim();
const nodes = (root) => root.querySelectorAll('script[type="application/ld+json"]').flatMap((s) => { const d = JSON.parse(s.text); return d['@graph'] ?? [d]; });
const fields = (line) => (line.match(/("([^"]|"")*"|[^,]*)(,|$)/g) ?? []).slice(0, -1).map((x) => x.replace(/,$/, '').replace(/^"(.*)"$/, '$1').replace(/""/g, '"'));

if (!existsSync(join(RAW, 'SOURCE.md'))) { console.log('check-energy: no data/raw/energy, skipped'); process.exit(0); }
const gen = JSON.parse(readFileSync('src/data/energy/index.json', 'utf8'));
const un = new Set(JSON.parse(readFileSync('src/data/wpp/index.json', 'utf8')).countries.map((c) => c.iso3));

// ---- 1. data = original files ----
const want = new Map(); // `${iso}|${key}|${year}` -> value
const put = (iso, k, y, v) => { if (v !== '' && v != null) want.set(`${iso}|${k}|${y}`, Number(v)); };
{
  const lines = readFileSync(join(RAW, gen.meta.gcb.file), 'utf8').split(/\r?\n/).filter(Boolean);
  const h = fields(lines[0]);
  const I = (n) => h.indexOf(n);
  for (const l of lines.slice(1)) {
    const f = fields(l); let iso = f[I('ISO 3166-1 alpha-3')]; const y = f[I('Year')];
    if (iso === 'WLD') { put('WORLD', 'co2', y, f[I('Total')]); put('WORLD', 'co2pc', y, f[I('Per Capita')]); continue; }
    if (iso === 'KSV') iso = 'XKX';
    if (!un.has(iso)) continue;
    put(iso, 'co2', y, f[I('Total')]);
    if (f[I('Per Capita')] !== '' && Number(f[I('Per Capita')]) !== 0) put(iso, 'co2pc', y, f[I('Per Capita')]);
  }
}
{
  const MAP = { 'Total generation': [['gen', 'Generation (TWh)']], Renewables: [['ren', 'Generation (TWh)'], ['renShare', 'Share of generation (%)']], 'Wind and solar': [['ws', 'Generation (TWh)'], ['wsShare', 'Share of generation (%)']], Fossil: [['fossilShare', 'Share of generation (%)']], Hydro: [['hydroShare', 'Share of generation (%)']], 'Other renewables': [['otherRenShare', 'Share of generation (%)']] };
  const lines = readFileSync(join(RAW, gen.meta.ember.file), 'utf8').split(/\r?\n/).filter(Boolean);
  const h = fields(lines[0]); const I = (n) => h.indexOf(n);
  for (const l of lines.slice(1)) {
    const f = fields(l); const m = MAP[f[I('Electricity source')]]; if (!m) continue;
    const iso = f[I('Area type')] === 'Country or economy' ? f[I('ISO 3 code')] : f[I('Area')] === 'World' ? 'WORLD' : null;
    if (!iso || (iso !== 'WORLD' && !un.has(iso))) continue;
    for (const [k, col] of m) put(iso, k, f[I('Year')], f[I(col)]);
  }
}
let got = 0;
const ents = [...Object.values(gen.countries).map((c) => [c.iso3, c.series]), ['WORLD', gen.world.series]];
for (const [iso, series] of ents) {
  ok(iso === 'WORLD' || un.has(iso), 'data', `${iso} is not on the UN list`);
  for (const [k, s] of Object.entries(series)) for (const [y, v] of s) {
    got++;
    const w = want.get(`${iso}|${k}|${y}`);
    if (w !== v) problems.push(`data: ${iso} ${k} ${y} = ${v}, original file ${w}`);
  }
}
ok(got === want.size, 'data', `generated data holds ${got} values, original files ${want.size}`);
checks += got;

// ---- 2. ranking pages ----
const sitemap = readFileSync(join(DIST, 'sitemap.xml'), 'utf8');
const lastmod = (u) => (sitemap.match(new RegExp(`<loc>[^<]*${BASE}${u.replace(/\//g, '\\/')}</loc><lastmod>([^<]+)</lastmod>`)) || [])[1];
const valueOf = (iso, k, y) => want.get(`${iso}|${k}|${y}`);
const yearOf = (k) => { // latest year with values for >= 90% of the countries that have the series
  const per = new Map(); const has = new Set();
  for (const key of want.keys()) { const [iso, kk, y] = key.split('|'); if (kk !== k || iso === 'WORLD') continue; has.add(iso); per.set(y, (per.get(y) ?? 0) + 1); }
  const max = Math.max(...per.values());
  return Math.max(...[...per].filter(([, n]) => n >= 0.9 * max).map(([y]) => Number(y)));
};
const one = (v) => v.toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const PAGES = {
  'co2-emissions-by-country': { key: 'co2', cell: one, csvCol: 'co2_million_tonnes', lic: gen.meta.gcb.licenceUrl },
  'renewable-electricity-by-country': { key: 'renShare', cell: (v) => `${Math.min(v, 100).toFixed(1)}%`, csvCol: 'renewables_share_of_generation_pct', lic: gen.meta.ember.licenceUrl },
};
for (const [slug, P] of Object.entries(PAGES)) {
  const url = `/rankings/${slug}/`, where = `page ${url}`;
  const file = join(DIST, 'rankings', slug, 'index.html');
  if (!ok(existsSync(file), where, 'page not built')) continue;
  const html = readFileSync(file, 'utf8'); const root = parse(html);
  const text = textOf(parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, '')));
  const m = JSON.parse(readFileSync(`src/data/rankings/${slug}.json`, 'utf8'));
  const L = yearOf(P.key);
  const rows = [...un].map((iso) => ({ iso3: iso, v: valueOf(iso, P.key, L) })).filter((x) => x.v != null).sort((a, b) => b.v - a.v || a.iso3.localeCompare(b.iso3));
  ok(text.includes(`, ${L}`), where, `ranking year ${L} not shown`);
  const trs = root.querySelectorAll('table.ranking tbody tr');
  ok(trs.length === rows.length, where, `ranking has ${trs.length} rows, original files ${rows.length} with ${L} data`);
  trs.forEach((tr, i) => {
    const w = rows[i]; if (!w) return;
    ok(tr.getAttribute('data-iso3') === w.iso3 && Number(tr.getAttribute('data-rank')) === i + 1, where, `row ${i + 1}: ${tr.getAttribute('data-iso3')} ≠ ${w.iso3}`);
    ok(textOf(tr.querySelector('td.c-val')) === P.cell(w.v), where, `row ${w.iso3}: value ${textOf(tr.querySelector('td.c-val'))} ≠ ${P.cell(w.v)}`);
    const img = tr.querySelector('th.c-name img.flag'), none = tr.querySelector('th.c-name .flag-none');
    ok(img || none, where, `row ${w.iso3}: no flag`);
    if (img) { const src = img.getAttribute('src') ?? ''; ok(src.startsWith(BASE + '/') && existsSync(join(DIST, src.slice(BASE.length))) && img.getAttribute('alt') === '', where, `row ${w.iso3}: flag file missing or alt not empty`); }
  });
  const mapEl = root.querySelector('[data-worldmap]');
  if (ok(mapEl, where, 'no world map')) {
    const rankOf = new Map(rows.map((w, i) => [w.iso3, i + 1]));
    const items = mapEl.querySelectorAll('[data-iso3]'); const seen = new Set();
    for (const it of items) { const iso = it.getAttribute('data-iso3'); ok(!seen.has(iso) && rankOf.get(iso) === Number(it.getAttribute('data-r')), where, `map ${iso}: duplicate or rank ≠ table`); seen.add(iso); }
    const counts = mapEl.querySelectorAll('.map-legend .ct').map((c) => Number(textOf(c).replace(/[()]/g, '')));
    ok(counts.reduce((a, b) => a + b, 0) === rows.length, where, 'map legend counts ≠ ranking');
  }
  const n = nodes(root);
  const art = n.find((x) => x['@type'] === 'Article'), il = n.find((x) => x['@type'] === 'ItemList'), ds = n.find((x) => x['@type'] === 'Dataset'), fq = n.find((x) => x['@type'] === 'FAQPage');
  if (!ok(art && il && ds && fq, where, 'needs Article + ItemList + Dataset + FAQPage')) continue;
  const names = trs.map((tr) => textOf(tr.querySelector('th.c-name')).replace(textOf(tr.querySelector('th.c-name .reg')), '').trim());
  ok(JSON.stringify(il.itemListElement.map((x) => x.name)) === JSON.stringify(names) && il.itemListElement.every((x, i) => x.position === i + 1), where, 'ItemList ≠ ranking shown');
  for (const t of [art.headline, art.description, ds.name, ds.description, ...fq.mainEntity.flatMap((q) => [q.name, q.acceptedAnswer.text])]) {
    for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
  }
  ok(JSON.stringify(root.querySelectorAll('.faq details summary').map(textOf)) === JSON.stringify(fq.mainEntity.map((q) => q.name)), where, 'FAQ in JSON-LD differs from the page');
  ok(ds.license === 'https://creativecommons.org/licenses/by/4.0/' && P.lic === ds.license, where, 'Dataset licence is not CC BY 4.0');
  ok(art.dateModified?.startsWith(m.updated) && lastmod(url) === m.updated && root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === m.updated), where, 'Updated ≠ dateModified / sitemap / shown date');
  const csvPath = join(DIST, (ds.distribution?.[0]?.contentUrl ?? '').replace(/^https?:\/\/[^/]+/, '').slice(BASE.length));
  if (ok(existsSync(csvPath), where, 'Dataset CSV missing')) {
    const lines = readFileSync(csvPath, 'utf8').split('\n').filter((l) => l && !l.startsWith('#'));
    const head = fields(lines[0]); const ci = head.indexOf(P.csvCol), ii = head.indexOf('iso3');
    ok(lines.length - 1 === rows.length, where, 'CSV row count ≠ ranking');
    lines.slice(1).forEach((l, i) => { const f = fields(l); ok(f[ii] === rows[i]?.iso3 && Number(f[ci]) === rows[i]?.v && Number(f[0]) === i + 1, where, `CSV row ${i + 1} ≠ original file`); });
  }
  for (const el of root.querySelectorAll('article .answer, article .prose p, article .faq p')) {
    const t = textOf(el); checks++;
    for (const x of t.match(/\d+\.\d{2,}%/g) ?? []) problems.push(`${where}: percent with more than 1 decimal in prose: "${x}"`);
    for (const x of t.match(/\b\d{1,3}(,\d{3}){2,}\b/g) ?? []) problems.push(`${where}: full number "${x}" in prose`);
  }
}

if (problems.length) {
  console.log(`\n✗ Energy check: ${problems.length} problem(s)\n`);
  for (const p of problems.slice(0, 60)) console.log('  - ' + p);
  process.exit(1);
}
console.log(`✓ Energy data = original files (${got} values) and ${Object.keys(PAGES).length} ranking pages passed: ${checks} checks (rows, values, flags, map, schema, CSV, dates, style).`);
