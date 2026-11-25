// Site-wide automatic checks. Runs after `astro build` (part of `npm run check` and CI).
// Usage: node scripts/check-site.mjs [distDir]
//
//  1. Data      — generated src/data/wpp/ equals the ORIGINAL UN files (independent parse, every country, every year)
//  2. Figures   — on every country page: key figures from the data appear on the page; every number in the
//                 JSON-LD text also appears on the page; the CSV equals the data
//  3. Style     — number style in prose (percent 1 decimal, millions 1 decimal, no full 7+ digit numbers in prose)
//  4. Schema    — valid JSON-LD; required types per page; ISO dates with time zone; Updated date = dateModified
//                 = sitemap lastmod; FAQ in schema = FAQ on the page; Dataset CSV exists
//  5. Links     — every internal link and #anchor resolves
//  6. Rules     — live counters carry "Estimate based on UN projections"; FAQ and Sources start closed;
//                 Sources has "Report an error"; noindex pages are not in the sitemap; sitemap pages exist
// Exit code 1 if anything fails, with a plain list of what and where.

import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { gunzipSync } from 'node:zlib';
import { execFileSync } from 'node:child_process';
import { parse } from 'node-html-parser';

const DIST = process.argv[2] || 'dist';
const BASE = '/atlasfigures';
const CURRENT_YEAR = 2026;
const problems = [];
const fail = (where, what) => problems.push(`${where}: ${what}`);
let checks = 0;
const ok = (cond, where, what) => { checks++; if (!cond) fail(where, what); return cond; };

// ---------- helpers ----------
const walk = (d) => readdirSync(d).flatMap((f) => { const p = join(d, f); return statSync(p).isDirectory() ? walk(p) : [p]; });
const pages = walk(DIST).filter((f) => f.endsWith('.html'));
const urlOf = (file) => file.slice(DIST.length).replace(/index\.html$/, '').replace(/\\/g, '/') || '/';
const textOf = (el) => el.text.replace(/\s+/g, ' ').trim();
const int = (v) => Math.round(v).toLocaleString('en-US');
const pct = (v) => `${v.toFixed(1)}%`;
const millions = (v) => `${(v / 1e6).toFixed(1)} million`;
const ord = (n) => { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); };
const jsonld = (root) => root.querySelectorAll('script[type="application/ld+json"]').map((s) => JSON.parse(s.text));
const nodes = (ld) => ld.flatMap((d) => d['@graph'] ?? [d]);

// ---------- 1. Data: generated files vs original UN files (independent parse) ----------
function parseCsvLine(line) {
  const out = []; let cur = ''; let q = false;
  for (const ch of line) {
    if (ch === '"') q = !q; else if (ch === ',' && !q) { out.push(cur); cur = ''; } else cur += ch;
  }
  out.push(cur); return out;
}
{
  const raw = gunzipSync(readFileSync('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz')).toString('utf8').replace(/^﻿/, '').split('\n');
  const head = parseCsvLine(raw[0].trim());
  const col = (n) => head.indexOf(n);
  const upd = execFileSync('unzip', ['-p', 'data/raw/un-wpp-2024/WPP2024_CSV_files_update.zip', 'WPP2024_Demographic_Indicators_Medium_Update.csv'], { maxBuffer: 1 << 28 }).toString('utf8').replace(/^﻿/, '').split('\n');
  const updLocs = new Set(upd.slice(1).filter(Boolean).map((l) => parseCsvLine(l.trim())[col('LocID')]));
  const tag = (lines, isUpd) => lines.filter((l) => l.trim()).map((l) => ({ r: parseCsvLine(l.trim()), isUpd }));
  const rows = [...tag(raw.slice(1), false), ...tag(upd.slice(1), true)];
  const want = new Map(); // ISO3:year → row
  for (const { r, isUpd } of rows) {
    if (r[col('LocTypeName')] !== 'Country/Area' || !r[col('TPopulation1July')]) continue;
    if (updLocs.has(r[col('LocID')]) && !isUpd) continue; // interim update replaces these rows
    want.set(`${r[col('ISO3_code')]}:${r[col('Time')]}`, r);
  }
  const dir = 'src/data/wpp/countries';
  let n = 0;
  for (const f of readdirSync(dir)) {
    const d = JSON.parse(readFileSync(join(dir, f), 'utf8'));
    for (const y of d.years) {
      const r = want.get(`${d.iso3}:${y.year}`);
      if (!ok(r, `data ${d.iso3} ${y.year}`, 'year missing in the UN file')) continue;
      n++;
      const pop = Math.round(Number(r[col('TPopulation1July')]) * 1000);
      ok(y.population === pop, `data ${d.iso3} ${y.year}`, `population ${y.population} ≠ UN ${pop}`);
      ok(Math.abs(y.fertility - Number(r[col('TFR')])) < 1e-9, `data ${d.iso3} ${y.year}`, 'fertility differs from UN file');
      ok(Math.abs(y.medianAge - Number(r[col('MedianAgePop')])) < 1e-9, `data ${d.iso3} ${y.year}`, 'median age differs from UN file');
      ok(Math.abs(y.densityPerKm2 - Number(r[col('PopDensity')])) < 1e-9, `data ${d.iso3} ${y.year}`, 'density differs from UN file');
      ok(y.change === Math.round(Number(r[col('PopChange')]) * 1000), `data ${d.iso3} ${y.year}`, 'yearly change differs from UN file');
    }
  }
  ok(n > 237 * 140, 'data', `only ${n} country-years compared`);
}
// WUP urban share: spot check every country, current year, against the xlsx (independent regex read)
{
  const zip = 'data/raw/un-wup-2025/WUP2025-F15-National-Definitions_percPop_by_category.xlsx';
  const u = (m) => execFileSync('unzip', ['-p', zip, m], { maxBuffer: 1 << 28 }).toString('utf8');
  const wb = u('xl/workbook.xml'); const rels = u('xl/_rels/workbook.xml.rels');
  const rid = wb.match(/<sheet[^>]*name="Urban"[^>]*r:id="([^"]+)"/)[1];
  const target = (rels.match(new RegExp(`Id="${rid}"[^>]*Target="([^"]+)"`)) || rels.match(new RegExp(`Target="([^"]+)"[^>]*Id="${rid}"`)))[1];
  const shared = [...u('xl/sharedStrings.xml').matchAll(/<si>([\s\S]*?)<\/si>/g)].map((m) => [...m[1].matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join(''));
  const sheet = u('xl/' + target.replace(/^\/?xl\//, ''));
  const cell = (c) => { const v = c.match(/<v>([^<]*)<\/v>/)?.[1]; return /t="s"/.test(c) ? shared[Number(v)] : v; };
  const rowsX = [...sheet.matchAll(/<row[^>]*>([\s\S]*?)<\/row>/g)].map((r) => Object.fromEntries([...r[1].matchAll(/<c r="([A-Z]+)\d+"[^>]*?(?:\/>|>[\s\S]*?<\/c>)/g)].map((m) => [m[1], cell(m[0])])));
  const headX = rowsX[0];
  const colOf = (name) => Object.keys(headX).find((k) => headX[k] === name);
  const isoCol = colOf('ISO3_Code'), yCol = colOf(String(CURRENT_YEAR));
  for (const r of rowsX.slice(1)) {
    const iso = r[isoCol]; if (!iso || !existsSync(`src/data/wpp/countries/${iso}.json`)) continue;
    const d = JSON.parse(readFileSync(`src/data/wpp/countries/${iso}.json`, 'utf8'));
    const y = d.years.find((x) => x.year === CURRENT_YEAR);
    ok(Math.abs((y.urbanPct ?? NaN) - Number(r[yCol])) < 1e-9, `data ${iso} ${CURRENT_YEAR}`, 'urban share differs from UN WUP file');
  }
}

// ---------- page-level checks ----------
const sitemap = readFileSync(join(DIST, 'sitemap.xml'), 'utf8');
const sitemapUrls = [...sitemap.matchAll(/<loc>([^<]+)<\/loc><lastmod>([^<]+)<\/lastmod>/g)].map((m) => ({ loc: m[1], lastmod: m[2] }));
const ids = new Map(pages.map((f) => [urlOf(f), new Set([...readFileSync(f, 'utf8').matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]))]));
const countries = readdirSync('src/data/countries').map((f) => JSON.parse(readFileSync(join('src/data/countries', f), 'utf8')));

for (const file of pages) {
  const url = urlOf(file);
  const html = readFileSync(file, 'utf8');
  const root = parse(html);
  const where = `page ${url}`;
  const noindex = root.querySelector('html')?.getAttribute('data-page-noindex') === 'true';
  const visible = parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, ''));
  const text = textOf(visible);

  // 4. Schema
  let ld = [];
  try { ld = jsonld(root); } catch (e) { fail(where, `JSON-LD does not parse: ${e.message}`); }
  const types = nodes(ld).map((n) => n['@type']);
  ok(types.includes('Organization') && types.includes('WebSite'), where, 'JSON-LD missing Organization/WebSite');
  if (root.querySelector('nav.crumbs')) ok(types.includes('BreadcrumbList'), where, 'breadcrumb shown but no BreadcrumbList');
  for (const n of nodes(ld)) for (const k of ['datePublished', 'dateModified']) {
    if (n[k]) ok(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?[+-]\d{2}:\d{2}$/.test(n[k]), where, `${n['@type']}.${k} "${n[k]}" is not an ISO datetime with time zone`);
  }
  if (/\/(time|economy|rankings|more)\/$/.test(url)) ok(noindex, where, 'coming-soon / navigation page must be noindex');

  // 5. Links
  for (const a of root.querySelectorAll('a[href]')) {
    const href = a.getAttribute('href');
    if (/^(https?:|mailto:|tel:)/.test(href)) continue;
    const [p, hash] = href.split('#');
    const targetUrl = p === '' ? url : p.startsWith(BASE) ? p.slice(BASE.length) || '/' : null;
    if (targetUrl === null) { fail(where, `link outside the site base: ${href}`); continue; }
    const exists = ids.has(targetUrl) || existsSync(join(DIST, targetUrl));
    ok(exists, where, `broken link ${href}`);
    if (exists && hash && ids.has(targetUrl)) ok(ids.get(targetUrl).has(hash), where, `link ${href}: no element with id "${hash}"`);
  }

  // 6. Rules
  for (const live of root.querySelectorAll('section.live')) ok(textOf(live).includes('Estimate based on UN projections'), where, 'live counter without "Estimate based on UN projections"');
  for (const d of root.querySelectorAll('details')) ok(!d.hasAttribute('open'), where, 'a FAQ/Sources section starts open');
  const sources = root.querySelector('details#sources');
  if (sources) ok(/Report an error/.test(textOf(sources)), where, 'Sources section has no "Report an error" link');
  const inSitemap = sitemapUrls.find((s) => s.loc.endsWith(`${BASE}${url}`));
  if (noindex) ok(!inSitemap, where, 'noindex page is listed in the sitemap');

  // Country pages: 2 (figures), 3 (style), 4 (Article/Dataset/FAQ)
  const c = countries.find((x) => url === `/population/${x.slug}/`);
  if (!c) continue;
  const d = JSON.parse(readFileSync(`src/data/wpp/countries/${c.iso3}.json`, 'utf8'));
  const y = Object.fromEntries(d.years.map((r) => [r.year, r]));
  const now = y[CURRENT_YEAR];
  const expected = {
    'population': int(now.population), 'population (millions)': now.population >= 1e9 ? `${(now.population / 1e9).toFixed(2)} billion` : millions(now.population), 'world rank': ord(now.worldRank),
    'share of world': pct(now.worldSharePct), 'growth rate': pct(now.growthRatePct), 'yearly change': int(now.change),
    'density': int(now.densityPerKm2), 'land area': int(d.landAreaKm2), 'median age': now.medianAge.toFixed(1),
    'births per woman': now.fertility.toFixed(2), 'urban share': now.urbanPct == null ? null : pct(now.urbanPct),
  };
  for (const [k, v] of Object.entries(expected)) if (v) ok(text.includes(v), where, `${k} ${v} (from the UN data) is not on the page`);
  const liveEl = root.querySelector('section.live');
  if (liveEl) {
    ok(Number(liveEl.getAttribute('data-anchor')) === now.population, where, 'live counter anchor ≠ UN mid-year population');
    ok(Number(liveEl.getAttribute('data-rate')) === now.change, where, 'live counter rate ≠ UN yearly change');
    ok(liveEl.getAttribute('data-date') === `${CURRENT_YEAR}-07-01`, where, 'live counter does not start on 1 July');
  }
  // table rows
  for (const tr of root.querySelectorAll('table.data tbody tr')) {
    const cells = tr.querySelectorAll('th,td').map(textOf);
    const yr = Number(cells[0].match(/\d{4}/)?.[0]);
    if (y[yr]) ok(cells.some((t) => t.includes(int(y[yr].population))), where, `table ${yr}: population ≠ ${int(y[yr].population)}`);
  }
  // JSON-LD text numbers must appear on the page
  const art = nodes(ld).find((n) => n['@type'] === 'Article');
  const faqLd = nodes(ld).find((n) => n['@type'] === 'FAQPage');
  const dataset = nodes(ld).find((n) => n['@type'] === 'Dataset');
  ok(art && faqLd && dataset, where, 'country page needs Article + Dataset + FAQPage');
  const ldTexts = [art?.headline, art?.description, ...(faqLd?.mainEntity ?? []).flatMap((q) => [q.name, q.acceptedAnswer?.text])].filter(Boolean);
  for (const t of ldTexts) for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
  // FAQ in schema = FAQ shown
  const shownQ = root.querySelectorAll('.faq details summary').map(textOf);
  ok(JSON.stringify(shownQ) === JSON.stringify((faqLd?.mainEntity ?? []).map((q) => q.name)), where, 'FAQ questions in JSON-LD differ from those on the page');
  // dates: visible Updated = dateModified = sitemap lastmod
  const upd = c.updated;
  ok(art?.dateModified?.startsWith(upd), where, `Article dateModified ≠ Updated ${upd}`);
  ok(root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === upd), where, `Updated date ${upd} not shown on the page`);
  ok(inSitemap?.lastmod === upd, where, `sitemap lastmod ${inSitemap?.lastmod} ≠ Updated ${upd}`);
  // Dataset CSV exists and equals the data
  const csvUrl = dataset?.distribution?.[0]?.contentUrl;
  const csvPath = csvUrl && join(DIST, csvUrl.replace(/^https?:\/\/[^/]+/, '').slice(BASE.length));
  if (ok(csvPath && existsSync(csvPath), where, `Dataset CSV ${csvUrl} missing`)) {
    for (const line of readFileSync(csvPath, 'utf8').split('\n').filter((l) => /^\d{4},/.test(l))) {
      const [yr, pop, dens, tfr] = line.split(',');
      const r = y[Number(yr)];
      ok(r && Number(pop) === r.population && Number(dens) === Math.round(r.densityPerKm2) && Number(tfr) === Number(r.fertility.toFixed(2)), where, `CSV row ${yr} ≠ UN data`);
    }
  }
  // 3. Number style in prose
  const prose = visible.querySelectorAll('article .answer, article .prose p, article .faq p, article .age-row');
  for (const el of prose) {
    el.querySelectorAll('[data-exact]').forEach((x) => x.remove());
    const t = textOf(el);
    for (const m of t.match(/\d+\.\d{2,}%/g) ?? []) fail(where, `percent with more than 1 decimal in prose: "${m}"`);
    for (const m of t.match(/\b\d{1,3}(,\d{3}){2,}\b/g) ?? []) fail(where, `full number "${m}" in prose; write it as "x.x million" (or mark an exact count with data-exact)`);
    // Measured figures in millions need exactly 1 decimal; round thresholds ("more than 10 million people") are fine.
    for (const m of t.matchAll(/(?<![\d.,])(\d+(?:\.\d+)?) million/g)) {
      const before = t.slice(Math.max(0, m.index - 10), m.index);
      // Round thresholds and milestones ("more than 10 million", "crossed 100 million") are not measured figures.
      if (/(than|over|under|least) $/.test(before) && /^\d+$/.test(m[1])) continue;
      if (/(pass|passes|passed|crossed|reach|reaches|reached|past|above|below|the) $/.test(before) && /^\d+0$/.test(m[1])) continue;
      if (!/^\d+\.\d$/.test(m[1])) fail(where, `"${m[0]}": millions need exactly 1 decimal`);
    }
  }
  for (const t of [root.querySelector('title')?.text ?? '', root.querySelector('meta[name="description"]')?.getAttribute('content') ?? '']) {
    for (const m of t.match(/\d+\.\d{2,}%/g) ?? []) fail(where, `percent with more than 1 decimal in title/description: "${m}"`);
  }
  checks += prose.length;
}

// sitemap entries must be real pages
for (const s of sitemapUrls) {
  const u = s.loc.replace(/^https?:\/\/[^/]+/, '').slice(BASE.length);
  ok(ids.has(u), 'sitemap', `${s.loc} is not a built page`);
}

if (problems.length) {
  console.log(`\n✗ Site check: ${problems.length} problem(s)\n`);
  for (const p of problems) console.log('  - ' + p);
  process.exit(1);
}
console.log(`✓ Site check passed: ${checks} checks on ${pages.length} pages (data vs UN files, figures, style, schema, links, rules).`);
