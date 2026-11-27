// new-ranking (task 149): add a World Bank indicator and its ranking page in one go, so nothing is forgotten.
//
// Step 1 — the data (then push to dev-data: the "Fetch World Bank data" workflow downloads the zip,
//          checks its licence is CC BY 4.0 and commits it; run `npm run data` after pulling):
//   node scripts/tools/new-ranking.mjs indicator --code SH.MED.PHYS.ZS --key doctorsPer1000 \
//        --label "Physicians" --unit "per 1,000 people"
//
//   node scripts/tools/new-ranking.mjs indicators --from phase-a.json      # many at once
//
// Step 2 — the page (after the data is in):
//   node scripts/tools/new-ranking.mjs page --slug doctors-per-1000-by-country --key doctorsPer1000 \
//        --topic health --title "Doctors per 1,000 people by country" --short "Doctors" \
//        --blurb "Physicians per 1,000 people, from …" --fmt dec1 --unit-label "per 1,000 people" \
//        --leader "Most doctors" --csv-col physicians_per_1000_people [--since 2015] [--coverage] [--source "WHO via World Bank"]
//
// Step 2 writes: the page scaffold (src/pages/rankings/<slug>.astro, text marked WRITE, build blocked until
// written), its editorial JSON, the CSV entry, the check-econ-pages entry, the catalog card and the sitemap line.
// Formats (--fmt): pct (12.3%), dec1 (12.3), int (1,234), usd ($1.2 billion), whole ($1,234).
import { readFileSync, writeFileSync, existsSync } from 'node:fs';

const [cmd, ...rest] = process.argv.slice(2);
const a = {};
for (let i = 0; i < rest.length; i++) { const k = rest[i].replace(/^--/, ''); const v = rest[i + 1]; if (!v || v.startsWith('--')) a[k] = true; else { a[k] = v; i++; } }
const need = (...ks) => { for (const k of ks) if (!a[k]) { console.error(`missing --${k}`); process.exit(2); } };
const today = new Date(Date.now() + 6 * 3600e3).toISOString().slice(0, 10); // Dhaka date
const edit = (file, fn) => { const s = readFileSync(file, 'utf8'); const t = fn(s); if (t === s) throw new Error(`${file}: nothing changed`); writeFileSync(file, t); console.log(`  ✓ ${file}`); };
const insertBefore = (s, anchorStart, closing, text) => {
  const i = s.indexOf(anchorStart); if (i < 0) throw new Error(`anchor not found: ${anchorStart}`);
  const j = s.indexOf(closing, i); if (j < 0) throw new Error(`closing not found after ${anchorStart}`);
  return s.slice(0, j) + text + s.slice(j);
};
const q = (x) => `'${String(x).replace(/\\/g, '\\\\').replace(/'/g, "\\'")}'`;

const FMT = {
  pct: { page: 'pct', catalog: 'pct', cell: '(v) => `${v.toFixed(1)}%`' },
  dec1: { page: '(v: number) => v.toFixed(1)', catalog: '(v) => v.toFixed(1)', cell: '(v) => v.toFixed(1)' },
  int: { page: 'int', catalog: "(v) => Math.round(v).toLocaleString('en-US')", cell: "(v) => Math.round(v).toLocaleString('en-US')" },
  usd: { page: "(v: number) => (v >= 1e12 ? `$${(v / 1e12).toFixed(2)} trillion` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)} billion` : `$${(v / 1e6).toFixed(1)} million`)", catalog: 'usd', cell: "(v) => (v >= 1e12 ? `$${(v / 1e12).toFixed(2)} trillion` : v >= 1e9 ? `$${(v / 1e9).toFixed(1)} billion` : `$${(v / 1e6).toFixed(1)} million`)" },
  whole: { page: "(v: number) => `$${Math.round(v).toLocaleString('en-US')}`", catalog: 'usdWhole', cell: 'whole' },
};

function addIndicator(x, quiet = false) {
  const txt = 'data/wdi-indicators.txt';
  if (readFileSync(txt, 'utf8').split('\n').includes(x.code)) throw new Error(`${x.code} already listed`);
  if (readFileSync('src/lib/econ.ts', 'utf8').includes(`'${x.key}'`)) throw new Error(`key ${x.key} already used`);
  edit(txt, (s) => s.replace(/\n*$/, `\n${x.code}\n`));
  edit('scripts/build-wdi.mjs', (s) => insertBefore(s, 'export const LABELS = {', '\n};', `\n  ${q(x.code)}: { key: ${q(x.key)}, label: ${q(x.label)}, unit: ${q(x.unit)} },`));
  edit('src/lib/econ.ts', (s) => insertBefore(s, 'export type IndicatorKey =', ';', ` | ${q(x.key)}`));
  if (!quiet) console.log(`\nNext: commit and push to dev-data → the fetch workflow downloads ${x.code} (fails unless CC BY 4.0).\nThen git pull, npm run data, and step 2 (page).`);
}
if (cmd === 'indicator') {
  need('code', 'key', 'label', 'unit');
  addIndicator(a);
} else if (cmd === 'indicators') {
  // many at once: --from list.json = [{"code": …, "key": …, "label": …, "unit": …}, …]
  need('from');
  const list = JSON.parse(readFileSync(a.from, 'utf8'));
  for (const x of list) { console.log(`${x.code} → ${x.key}`); addIndicator(x, true); }
  console.log(`\n${list.length} indicators added. Commit and push to dev-data → one fetch run downloads all of them.`);
} else if (cmd === 'page') {
  need('slug', 'key', 'topic', 'title', 'short', 'blurb', 'fmt', 'unit-label', 'leader', 'csv-col');
  const F = FMT[a.fmt]; if (!F) throw new Error(`--fmt must be one of ${Object.keys(FMT).join(', ')}`);
  const pageFile = `src/pages/rankings/${a.slug}.astro`, metaFile = `src/data/rankings/${a.slug}.json`;
  if (existsSync(pageFile) || existsSync(metaFile)) throw new Error(`${a.slug} already exists`);
  const meta = JSON.parse(readFileSync('src/data/wdi/meta.json', 'utf8'));
  const M = meta.indicators[a.key]; if (!M) throw new Error(`no generated data for ${a.key} — run step 1, fetch, npm run data`);
  if (!new RegExp(`key: '${a.topic}'`).test(readFileSync('src/lib/catalog.ts', 'utf8'))) throw new Error(`topic '${a.topic}' not in TOPICS (src/lib/catalog.ts) — add it there first`);
  const since = a.since ? Number(a.since) : null;
  const rankSetup = since
    ? `const ranked = rankLatest('${a.key}', ${since});\nconst L = Math.max(...ranked.map((r) => r.year)); // each economy at its latest year from ${since}`
    : a.coverage ? `const L = coverageYear('${a.key}');\nconst ranked = rankBy('${a.key}', L);` : `const L = rankingYear('${a.key}');\nconst ranked = rankBy('${a.key}', L);`;
  const tpl = readFileSync('scripts/tools/templates/ranking.astro.tpl', 'utf8')
    .replaceAll('{{SLUG}}', a.slug).replaceAll('{{KEY}}', a.key).replaceAll('{{TITLE}}', a.title.replace(/'/g, '’')).replaceAll('{{SHORT}}', a.short)
    .replaceAll('{{FMT}}', F.page).replaceAll('{{CODE}}', M.code).replaceAll('{{VALUELABEL}}', a['unit-label'])
    .replaceAll('{{RANKFN}}', since ? 'rankLatest' : a.coverage ? 'rankBy, coverageYear' : 'rankBy').replaceAll('{{RANKSETUP}}', rankSetup);
  writeFileSync(pageFile, tpl); console.log(`  ✓ ${pageFile} (scaffold — write every WRITE)`);
  writeFileSync(metaFile, JSON.stringify({ slug: a.slug, published: today, updated: today, changelog: [{ date: today, type: 'published', note: `First version: ${M.wbName}, World Bank WDI.` }] }, null, 2) + '\n');
  console.log(`  ✓ ${metaFile} (add "verification" after the hand check)`);
  const extra = [since ? ` since: ${since},` : '', a.coverage ? ' coverage: true,' : ''].join('');
  edit('src/pages/data/[ranking].csv.ts', (s) => insertBefore(s, 'const RANKINGS', '\n};\n', `\n  ${q(a.slug)}: { key: ${q(a.key)},${extra} cols: [\n    [${q(a['csv-col'])}, (x, y) => valueIn(econData(x).series.${a.key}, y)],\n  ] },`));
  edit('scripts/check-econ-pages.mjs', (s) => { const i = s.indexOf('\nconst wdiAll'); const j = s.lastIndexOf('};', i); return s.slice(0, j) + `,\n  ${q(a.slug)}: { key: ${q(a.key)}, cell: ${F.cell}, csvCol: ${q(a['csv-col'])}${since ? `, since: ${since}` : ''}${a.coverage ? ', coverage: true' : ''} } ` + s.slice(j); });
  edit('src/lib/catalog.ts', (s) => {
    const lines = s.split('\n'); const i = lines.map((l, k) => (l.trimStart().startsWith("wb('") ? k : -1)).filter((k) => k >= 0).at(-1);
    const opts = [a.coverage ? 'coverage: true' : '', `unit: ${q(a['unit-label'])}`, `leaderLabel: ${q(a.leader)}`, a.source ? `source: ${q(a.source)}` : ''].filter(Boolean).join(', ');
    lines.splice(i + 1, 0, `    wb(${q(a.slug)}, ${q(a.topic)}, ${q(a.title)}, ${q(a.blurb)}, ${q(a.key)}, ${F.catalog}, { ${opts} }),`);
    return lines.join('\n');
  });
  edit('src/pages/sitemap.xml.ts', (s) => { const lines = s.split('\n'); const i = lines.map((l, k) => (/path: '\/rankings\/[a-z0-9-]+-by-country\/'/.test(l) ? k : -1)).filter((k) => k >= 0).at(-1); lines.splice(i + 1, 0, `  { path: '/rankings/${a.slug}/', lastmod: '${today}' },`); return lines.join('\n'); });
  console.log(`\nNext: node scripts/tools/find-facts.mjs <ISO3s> --only ${a.key} · write the page · phrase-check · npm run check · verify script.`);
} else {
  console.error('usage: new-ranking.mjs indicator --code … --key … --label … --unit …\n       new-ranking.mjs page --slug … --key … --topic … --title … --short … --blurb … --fmt pct|dec1|int|usd|whole --unit-label … --leader … --csv-col … [--since YEAR] [--coverage] [--source …]');
  process.exit(2);
}
