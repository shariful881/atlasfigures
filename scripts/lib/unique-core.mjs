// Uniqueness check: no two country pages may share wording.
// Shared core of scripts/check-unique.mjs and scripts/tools/phrase-check.mjs (task 149).
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

export const N = 6;
export const MIN_CONTENT_WORDS = 2;

export const UI_SELECTORS = [
  'script', 'style', 'svg', 'nav', 'header.site', 'footer',
  '.live', '.dates', '.segments', '.facts', '.facts-m', '.sheet',
  '.sources-details', '.vchip', '.legend', '.readout', '.chart-foot',
  '.tcard-foot', '.table-scroll', '.btn-ghost', '.visually-hidden', '.rank-tools', '.rank-empty', '.map-zoom', '.map-legend', '.map-tip', '.clock', '.tfacts', '.pfacts', '.pair-clocks', '.conv',
  '.stat-list', '.topic-chips', '.data-head', '.data-note', // country hub/topic UI (task 160)
];

export const STOP = new Set(`a an the and or but of in on at to for from by with as is are was were be been being it its this that these those than then there their they them he she his her we our you your i not no so if into about over under up down out more most less least very also just only per each every all any some such which who whom whose what when where why how will would can could may might should shall do does did has have had one two`.split(' '));

// country data keyed by slug
// Sections whose pages are written per country (each has its own editorial JSON folder).
// Pages are compared across ALL sections: an economy page may not reuse a population page's wording either.
export const SECTIONS = [['population', 'src/data/countries'], ['economy', 'src/data/economy'], ['rankings', 'src/data/rankings'], ['time', 'src/data/cities'], ['country', 'src/data/country-pages']];
const EXTRA = { population: ['src/data/pages'], time: ['src/data/pairs'] }; // non-country pages in the same section (the World page)
export const countries = {}; // section → slug → country
for (const [sec, dir] of SECTIONS) {
  countries[sec] = {};
  for (const dd of [dir, ...(EXTRA[sec] ?? [])]) {
    if (!existsSync(dd)) continue;
    for (const f of readdirSync(dd)) {
      if (!f.endsWith('.json')) continue;
      const d = JSON.parse(readFileSync(join(dd, f), 'utf8'));
      countries[sec][d.slug] = d;
    }
  }
}

const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

export function normalize(text, c) {
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

export function extract(file, slug) {
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


/** 6-word runs (with at least MIN_CONTENT_WORDS content words) of each block → the block they came from. */
export function grams(blocks, c) {
  const m = new Map();
  for (const b of new Set(blocks)) {
    const w = normalize(b, c);
    for (let i = 0; i + N <= w.length; i++) {
      const g = w.slice(i, i + N);
      const content = g.filter((x) => !x.startsWith('<') && !STOP.has(x)).length;
      if (content >= MIN_CONTENT_WORDS) m.set(g.join(' '), b);
    }
  }
  return m;
}

/** Every written page in the build (country, economy, ranking, time pages), with grams and headings. */
export function loadPages(DIST = 'dist') {
  const pages = [];
  for (const [sec] of SECTIONS) {
    if (sec === 'country') {
      // hubs (/country/<slug>/) and topic pages (/country/<slug>/<topic>/) written from task 160 on
      for (const [slug, c] of Object.entries(countries.country)) {
        for (const topic of Object.keys(c.pages ?? {})) {
          const file = topic === 'hub' ? join(DIST, 'country', slug, 'index.html') : join(DIST, 'country', slug, topic, 'index.html');
          if (!existsSync(file)) continue;
          const p = extract(file, topic === 'hub' ? `country/${slug}` : `${topic}/${slug}`);
          if (!p) continue;
          p.grams = grams(p.blocks, c);
          p.heads = new Map(p.headings.map((h) => [normalize(h, c).join(' '), h]));
          pages.push(p);
        }
      }
      continue;
    }
    for (const slug of Object.keys(countries[sec])) {
      // country pages live at /country/<slug>/<section>/ (task 148); the rest at /<section>/<slug>/
      const file = [join(DIST, 'country', slug, sec, 'index.html'), join(DIST, sec, slug, 'index.html')].find((f) => existsSync(f));
      if (!file) continue; // only written pages that were built
      const p = extract(file, `${sec}/${slug}`);
      if (!p) continue;
      const c = countries[sec][slug];
      p.grams = grams(p.blocks, c);
      p.heads = new Map(p.headings.map((h) => [normalize(h, c).join(' '), h]));
      pages.push(p);
    }
  }
  return pages;
}
