// phrase-check (task 149): catch shared wording BEFORE building — against every written page in the last
// build (dist/) and between the drafts themselves. Same rules as check-unique (scripts/lib/unique-core.mjs):
// a shared 6-word run with 2+ content words, or an identical heading/FAQ question, after the page's own
// country name, demonym and capital → <c>/<d>/<cap> and numbers → <n>.
//
// Drafts are .astro pages (text and string literals are read; {…} and ${…} count as a number) or .txt files
// (one block per line; lines starting "# " or "Q: " are headings / FAQ questions).
// Each draft needs its country words: from the matching editorial JSON (found by file name in
// src/data/{countries,economy,rankings,cities}/) or given with --names "Name|Demonym|Capital".
//
//   node scripts/tools/phrase-check.mjs src/pages/economy/denmark.astro src/pages/economy/finland.astro
//   node scripts/tools/phrase-check.mjs draft.txt --names "Denmark|Danish|Copenhagen"
//   node scripts/tools/phrase-check.mjs --bank [economy|population|rankings|time]   # headings already used
import { readFileSync, existsSync } from 'node:fs';
import { basename, dirname } from 'node:path';
import { loadPages, normalize, grams } from '../lib/unique-core.mjs';

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : null; };
const flag = (k) => { const i = args.indexOf(k); return i >= 0 ? (args.splice(i, 1), true) : false; };
const names = opt('--names');
const dist = opt('--dist') || 'dist';
const bank = flag('--bank');

if (!existsSync(`${dist}/population`)) { console.error(`No ${dist}/ — run a build once (the drafts are compared with the last build).`); process.exit(2); }
const pages = loadPages(dist);

if (bank) {
  // Every heading and FAQ question already used (normalised), most-used shapes first.
  const sec = args[0];
  const count = new Map();
  for (const p of pages) {
    if (sec && !p.slug.startsWith(sec + '/')) continue;
    for (const [k, h] of p.heads) { const e = count.get(k) ?? { n: 0, ex: h, pages: [] }; e.n++; e.pages.push(p.slug); count.set(k, e); }
  }
  const rows = [...count].sort((a, b) => b[1].n - a[1].n || a[0].localeCompare(b[0]));
  console.log(`# Headings and FAQ questions already used${sec ? ` in ${sec}` : ''} (${rows.length}) — every one is taken; write new ones\n`);
  for (const [k, e] of rows) console.log(`${String(e.n).padStart(2)}  ${k}    e.g. "${e.ex}" (${e.pages[0]})`);
  process.exit(0);
}

const SECTION_DIRS = { population: 'src/data/countries', economy: 'src/data/economy', rankings: 'src/data/rankings', time: 'src/data/cities' };
function countryWords(file) {
  if (names) { const [name, demonym, capital] = names.split('|'); return { name, demonym, capital }; }
  const slug = basename(file).replace(/\.(astro|txt)$/, '');
  const sec = basename(dirname(file));
  for (const dir of [SECTION_DIRS[sec], ...Object.values(SECTION_DIRS)].filter(Boolean)) {
    const j = `${dir}/${slug}.json`;
    if (existsSync(j)) { const d = JSON.parse(readFileSync(j, 'utf8')); if (d.name || d.demonym || d.capital) return d; }
  }
  // economy JSONs carry no names: borrow them from the population page's JSON
  const pj = `src/data/countries/${slug}.json`;
  if (existsSync(pj)) return JSON.parse(readFileSync(pj, 'utf8'));
  console.warn(`! ${file}: no country words found (use --names) — compared without replacing the name`);
  return {};
}

const unq = (s) => s.replace(/\$\{[^}]*\}/g, ' 0 ').replace(/\{[^{}]*\}/g, ' 0 ').replace(/\\'/g, "'").replace(/\s+/g, ' ').trim();
function readDraft(file) {
  const src = readFileSync(file, 'utf8')
    .replace(/assertClaim\([\s\S]*?\);\s*$/gm, '')        // claim labels are code, not page text
    .replace(/^\s*\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '') // comments
    .replace(/<details[^>]*sources-details[\s\S]*?<\/details>/g, '') // Sources accordion = shared UI (citations)
    .replace(/\b(licence|source|sourceUrl|estimateLabel|unit|note)\s*[=:]\s*\{?\{?\s*(name:\s*)?('[^']*'|"[^"]*"|`[^`]*`)/g, ''); // component props shown in card footers (UI)
  const blocks = [], heads = [];
  if (file.endsWith('.txt')) {
    for (const l of src.split('\n').map((x) => x.trim()).filter(Boolean)) {
      if (l.startsWith('# ') || l.startsWith('Q: ')) { heads.push(l.slice(2).trim()); blocks.push(l.slice(2).trim()); } else blocks.push(l);
    }
    return { blocks, heads };
  }
  // .astro: headings from markup and from h2:/q:/question:/title: keys; text from string literals and markup.
  for (const m of src.matchAll(/<(h[1-3]|summary)[^>]*>([\s\S]*?)<\/\1>/g)) heads.push(unq(m[2].replace(/<[^>]+>/g, ' ')));
  for (const m of src.matchAll(/\b(h2|h3|q|question|title|heading)\s*:\s*(`(?:[^`\\]|\\.)*`|'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")/g)) heads.push(unq(m[2].slice(1, -1)));
  for (const m of src.matchAll(/`(?:[^`\\]|\\.)*`|'(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*"/g)) {
    const t = unq(m[0].slice(1, -1).replace(/<[^>]+>/g, ' '));
    if (t.split(' ').length >= 6 && /[a-z]{3}/.test(t) && !/^[\w./-]+$/.test(t) && !t.includes('=>')) blocks.push(t);
  }
  const body = src.replace(/^---[\s\S]*?---/, '').replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, '');
  for (const m of body.matchAll(/>([^<>]{25,})</g)) { const t = unq(m[1]); if (t.split(' ').length >= 6) blocks.push(t); }
  return { blocks: [...blocks, ...heads], heads: heads.filter((h) => /[a-z]{3}/i.test(h) && h.split(' ').length >= 3) };
}

const files = args;
if (!files.length) { console.error('usage: phrase-check.mjs <draft.astro|draft.txt>... [--names "N|D|C"] | --bank [section]'); process.exit(2); }
const drafts = files.map((f) => {
  const c = countryWords(f);
  const { blocks, heads } = readDraft(f);
  const self = `${basename(dirname(f))}/${basename(f).replace(/\.(astro|txt)$/, '')}`;
  return { file: f, self, g: grams(blocks, c), h: new Map(heads.map((x) => [normalize(x, c).join(' '), x])) };
});

let problems = 0;
const report = (a, bName, shared, heads, bGrams) => {
  if (!shared.length && !heads.length) return;
  console.log(`\n✗ ${a.file}  ↔  ${bName}`);
  for (const h of heads) { console.log(`  same heading/question: "${a.h.get(h)}"`); problems++; }
  const seen = new Set();
  for (const g of shared) { const s = a.g.get(g); if (seen.has(s)) continue; seen.add(s); console.log(`  shared "${g}"\n    yours: "${s.slice(0, 150)}"\n    there: "${(bGrams.get(g) || '').slice(0, 150)}"`); problems++; }
};
for (const a of drafts) {
  for (const p of pages) {
    if (p.slug === a.self) continue; // the draft's own earlier build
    report(a, p.slug, [...a.g.keys()].filter((g) => p.grams.has(g)), [...a.h.keys()].filter((h) => h && p.heads.has(h)), p.grams);
  }
}
for (let i = 0; i < drafts.length; i++) for (let j = i + 1; j < drafts.length; j++) {
  const a = drafts[i], b = drafts[j];
  report(a, b.file, [...a.g.keys()].filter((g) => b.g.has(g)), [...a.h.keys()].filter((h) => h && b.h.has(h)), b.g);
}
console.log(`\nChecked ${drafts.length} draft(s) against ${pages.length} built page(s) and each other.`);
if (problems) { console.log(`${problems} problem(s) — reword before building.`); process.exit(1); }
console.log('✓ No shared wording found (check-unique still runs on the real build).');
