// Automatic check: generated World Bank data (src/data/wdi/) = the ORIGINAL World Bank files (data/raw/wdi/).
// Part of `npm run check` (and CI). Reads the original zips on its own, with its own parser — it does not
// reuse scripts/build-wdi.mjs — so a bug in the build cannot hide itself.
//
// Checks: indicator list ↔ files; licence CC BY-4.0 per indicator (API metadata); SHA-256 = SOURCE.md;
// every economy and aggregate, every indicator, every year: generated value === original value, and no
// value in the generated data that the original does not have; economy list and region/income group;
// WDI last-updated dates; index.json latest values.

import { readFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const RAW = 'data/raw/wdi';
const GEN = 'src/data/wdi';
const errors = [];
const fail = (m) => { if (errors.length < 50) errors.push(m); else if (errors.length === 50) errors.push('… more errors'); };

// Own CSV line splitter (World Bank files quote every field; no newlines inside the data rows we compare).
function splitLine(line) {
  const out = []; const re = /"((?:[^"]|"")*)"|([^,]*)/g; let m; let pos = 0;
  while (pos <= line.length) {
    re.lastIndex = pos; m = re.exec(line);
    out.push(m[1] != null ? m[1].replace(/""/g, '"') : m[2]);
    pos = re.lastIndex + 1;
    if (re.lastIndex >= line.length) break;
  }
  return out;
}
const unzip = (zip, name) => execFileSync('unzip', ['-p', zip, name], { maxBuffer: 1 << 28 }).toString('utf8').replace(/^﻿/, '');
const list = (zip) => execFileSync('unzip', ['-Z1', zip]).toString('utf8').split('\n').filter(Boolean);
const readJSON = (p) => JSON.parse(readFileSync(p, 'utf8'));

const codes = readFileSync('data/wdi-indicators.txt', 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
const source = readFileSync(join(RAW, 'SOURCE.md'), 'utf8');
if (!/Downloaded \(UTC\): \d{4}-\d\d-\d\dT/.test(source)) fail('SOURCE.md: no download time');
const meta = readJSON(join(GEN, 'meta.json'));
const index = readJSON(join(GEN, 'index.json'));
const aggs = new Map(readJSON(join(GEN, 'aggregates.json')).aggregates.map((a) => [a.code, a]));
const genFiles = new Set(readdirSync(join(GEN, 'countries')).map((f) => f.replace(/\.json$/, '')));

const rawFiles = readdirSync(RAW).filter((f) => f.endsWith('.zip')).map((f) => f.replace(/\.zip$/, ''));
for (const f of rawFiles) if (!codes.includes(f)) fail(`data/raw/wdi/${f}.zip is not in data/wdi-indicators.txt`);
if (Object.keys(meta.indicators).length !== codes.length) fail(`meta.json has ${Object.keys(meta.indicators).length} indicators, list has ${codes.length}`);

let compared = 0;
let economies = null;
for (const code of codes) {
  const zip = join(RAW, `${code}.zip`);
  const key = Object.keys(meta.indicators).find((k) => meta.indicators[k].code === code);
  if (!key) { fail(`${code}: not in generated meta.json`); continue; }
  const buf = readFileSync(zip);
  const hash = createHash('sha256').update(buf).digest('hex');
  if (!source.includes(`| ${hash} |`) || !source.includes(`| ${code} |`)) fail(`${code}: SHA-256 not recorded in SOURCE.md`);
  if (meta.indicators[key].sha256 !== hash) fail(`${code}: meta.json SHA-256 differs from the file`);
  const md = readJSON(join(RAW, `${code}.metadata.json`));
  const lic = md.source[0].concept[0].variable[0].metatype.find((m) => m.id === 'License_Type')?.value;
  if (lic !== 'CC BY-4.0') fail(`${code}: licence is "${lic}"`);

  const names = list(zip);
  const lines = unzip(zip, names.find((n) => n.startsWith('API_'))).split(/\r?\n/);
  const upd = splitLine(lines.find((l) => l.startsWith('"Last Updated Date"')) || '')[1];
  if (meta.indicators[key].wdiLastUpdated !== upd) fail(`${code}: last-updated ${meta.indicators[key].wdiLastUpdated} ≠ file ${upd}`);
  const hi = lines.findIndex((l) => l.startsWith('"Country Name"'));
  const head = splitLine(lines[hi]);

  if (!economies) {
    economies = new Map();
    const cl = unzip(zip, names.find((n) => n.startsWith('Metadata_Country_'))).split(/\r?\n/);
    // Country metadata notes can contain line breaks inside quotes: join until the field count is right.
    const ch = splitLine(cl[0]); let buf2 = '';
    for (const l of cl.slice(1)) {
      buf2 = buf2 ? `${buf2}\n${l}` : l;
      if ((buf2.match(/"/g) || []).length % 2) continue;
      const f = splitLine(buf2); buf2 = '';
      const o = Object.fromEntries(ch.map((h, i) => [h, f[i]]));
      if (o.Region) economies.set(o['Country Code'], o);
    }
    if (economies.size !== genFiles.size) fail(`economies: original ${economies.size}, generated ${genFiles.size}`);
    for (const [c, o] of economies) {
      if (!genFiles.has(c)) { fail(`${c}: no generated file`); continue; }
      const g = readJSON(join(GEN, 'countries', `${c}.json`));
      if (g.region !== o.Region || (g.incomeGroup || '') !== (o.IncomeGroup || '')) fail(`${c}: region/income group differs`);
    }
  }

  const seen = new Set();
  for (const l of lines.slice(hi + 1)) {
    if (!l.trim()) continue;
    const f = splitLine(l); const c = f[1];
    if (f[3] !== code) { fail(`${code}: row ${c} has code ${f[3]}`); continue; }
    seen.add(c);
    const g = economies.has(c) ? readJSON(join(GEN, 'countries', `${c}.json`)).series : aggs.get(c)?.series;
    if (!g) { fail(`${code}: ${c} missing from generated data`); continue; }
    const gen = new Map((g[key] || []).map(([y, v]) => [y, v]));
    let n = 0;
    head.forEach((h, i) => {
      if (!/^\d{4}$/.test(h) || f[i] === '' || f[i] == null) return;
      n++; compared++;
      const want = Number(f[i]); const got = gen.get(Number(h));
      if (got !== want) fail(`${code} ${c} ${h}: generated ${got}, original ${want}`);
    });
    if (gen.size !== n) fail(`${code} ${c}: generated has ${gen.size} years, original ${n}`);
  }
  for (const c of [...genFiles, ...aggs.keys()]) if (!seen.has(c)) fail(`${code}: ${c} in generated data but not in the original`);
}

// index.json = latest value of each series
for (const e of index.economies) {
  if (!genFiles.has(e.iso3)) continue;
  const g = readJSON(join(GEN, 'countries', `${e.iso3}.json`));
  for (const [k, s] of Object.entries(g.series)) {
    const want = s.length ? { year: s.at(-1)[0], value: s.at(-1)[1] } : null;
    if (JSON.stringify(e.latest[k]) !== JSON.stringify(want)) fail(`index.json ${e.iso3} ${k}: latest value differs`);
  }
}
if (index.economies.length !== genFiles.size) fail('index.json: economy count differs');

if (errors.length) {
  console.error(`✗ World Bank data check failed:\n  ${errors.join('\n  ')}`);
  process.exit(1);
}
console.log(`✓ World Bank data = original files: ${codes.length} indicators, ${economies.size} economies + ${aggs.size} aggregates, ${compared.toLocaleString('en-US')} values compared.`);
