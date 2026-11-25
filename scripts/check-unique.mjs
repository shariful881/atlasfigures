// Uniqueness check: no two country pages may share wording.
// Run after `astro build`:  node scripts/check-unique.mjs [distDir]
//
// What is compared: everything the editor writes for a page — <title>, meta
// description, H1, direct answer, story headings and paragraphs, chart and
// table titles/subtitles, FAQ questions and answers.
// What is NOT compared (shared site UI): live counter, Key facts labels,
// segment tabs, table cells, chart legend/axes, verified badges, the Sources
// and methodology accordion (citations), header/footer/nav.
//
// Each page's own country name, demonym and capital become <c>/<d>/<cap>,
// and every number becomes <n>, so "Japan has 123 million people" and
// "Bangladesh has 177.8 million people" count as the SAME wording.
//
// Fails when two pages share:
//   1. any 6-word run containing at least 2 content words, or
//   2. any identical heading or FAQ question (after the replacements above).

import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'node-html-parser';

const DIST = process.argv[2] || 'dist';
const N = 6;
const MIN_CONTENT_WORDS = 2;

const UI_SELECTORS = [
  'script', 'style', 'svg', 'nav', 'header.site', 'footer',
  '.live', '.dates', '.segments', '.facts', '.facts-m', '.sheet',
  '.sources-details', '.vchip', '.legend', '.readout', '.chart-foot',
  '.tcard-foot', '.table-scroll', '.btn-ghost', '.visually-hidden', '.rank-tools', '.rank-empty',
];

const STOP = new Set(`a an the and or but of in on at to for from by with as is are was were be been being it its this that these those than then there their they them he she his her we our you your i not no so if into about over under up down out more most less least very also just only per each every all any some such which who whom whose what when where why how will would can could may might should shall do does did has have had one two`.split(' '));

// country data keyed by slug
// Sections whose pages are written per country (each has its own editorial JSON folder).
// Pages are compared across ALL sections: an economy page may not reuse a population page's wording either.
const SECTIONS = [['population', 'src/data/countries'], ['economy', 'src/data/economy'], ['rankings', 'src/data/rankings']];
const countries = {}; // section → slug → country
for (const [sec, dir] of SECTIONS) {
  countries[sec] = {};
  if (!existsSync(dir)) continue;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith('.json')) continue;
    const d = JSON.parse(readFileSync(join(dir, f), 'utf8'));
    countries[sec][d.slug] = d;
  }
}

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function normalize(text, c) {
  let t = ' ' + text.toLowerCase().replace(/[‘’]/g, "'") + ' ';
  const subs = [];
  if (c?.demonym) subs.push([c.demonym, '<d>']);
  if (c?.name) subs.push([c.name, '<c>']);
  if (c?.capital) subs.push([c.capital, '<cap>']);
  for (const [w, tok] of subs.sort((a, b) => b[0].length - a[0].length)) {
    t = t.replace(new RegExp(`\\b${esc(w.toLowerCase())}s?('s)?\\b`, 'g'), ` ${tok} `);
  }
  t = t.replace(/\d[\d,.]*(st|nd|rd|th|%)?/g, ' <n> ');
  t = t.replace(/[^a-z<>' ]+/g, ' ').replace(/\s'|'\s/g, ' ');
  return t.split(/\s+/).filter(Boolean);
}

function extract(file, slug) {
  const root = parse(readFileSync(file, 'utf8'));
  const title = root.querySelector('title')?.text || '';
  const desc = root.querySelector('meta[name="description"]')?.getAttribute('content') || '';
  const main = root.querySelector('article.country-main') || root.querySelector('main');
  if (!main) return null;
  for (const sel of UI_SELECTORS) main.querySelectorAll(sel).forEach((el) => el.remove());
  const headings = main.querySelectorAll('h1, h2, h3').map((h) => h.text.trim()).filter(Boolean);
  const blocks = [title, desc, ...main.querySelectorAll('h1, h2, h3, p, li, figcaption, .chart-title, .chart-sub, .tcard-head h2, .tcard-sub, .age-row span')
    .map((el) => el.text.trim())];
  return { slug, headings, blocks };
}

if (!existsSync(join(DIST, 'population'))) { console.error(`No ${join(DIST, 'population')}. Run the build first.`); process.exit(2); }

const pages = [];
for (const [sec] of SECTIONS) {
 const pagesDir = join(DIST, sec);
 if (!existsSync(pagesDir)) continue;
 for (const slug of readdirSync(pagesDir)) {
  const file = join(pagesDir, slug, 'index.html');
  if (!existsSync(file) || !countries[sec][slug]) continue; // only country pages
  const p = extract(file, `${sec}/${slug}`);
  if (!p) continue;
  const c = countries[sec][slug];
  p.grams = new Map();
  for (const b of new Set(p.blocks)) {
    const w = normalize(b, c);
    for (let i = 0; i + N <= w.length; i++) {
      const g = w.slice(i, i + N);
      const content = g.filter((x) => !x.startsWith('<') && !STOP.has(x)).length;
      if (content >= MIN_CONTENT_WORDS) p.grams.set(g.join(' '), b);
    }
  }
  p.heads = new Map(p.headings.map((h) => [normalize(h, c).join(' '), h]));
  pages.push(p);
 }
}

let problems = 0;
for (let i = 0; i < pages.length; i++) {
  for (let j = i + 1; j < pages.length; j++) {
    const a = pages[i], b = pages[j];
    const shared = [...a.grams.keys()].filter((g) => b.grams.has(g));
    const heads = [...a.heads.keys()].filter((h) => b.heads.has(h));
    if (!shared.length && !heads.length) continue;
    console.log(`\n✗ ${a.slug} ↔ ${b.slug}`);
    for (const h of heads) { console.log(`  same heading: "${a.heads.get(h)}"  ↔  "${b.heads.get(h)}"`); problems++; }
    const seen = new Set();
    for (const g of shared) {
      const s = a.grams.get(g);
      if (seen.has(s)) continue; seen.add(s);
      console.log(`  shared wording "${g}"\n    in: "${s.slice(0, 140)}"`); problems++;
    }
  }
}

console.log(`\nChecked ${pages.length} country page(s).`);
if (problems) { console.log(`${problems} problem(s): rewrite these so each page says it in its own words.`); process.exit(1); }
console.log('✓ Every country page is written in its own words.');
