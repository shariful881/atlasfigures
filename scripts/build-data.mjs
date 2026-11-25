// Builds AtlasFigures' generated data from the ORIGINAL UN files in data/raw/un-wpp-2024/.
// Run: npm run data          (never edit the output by hand; re-run this instead)
//
// Input  : WPP2024_Demographic_Indicators_Medium.csv.gz (UN WPP 2024, 1950–2100, medium variant)
//          WPP2024_CSV_files_update.zip → *_Demographic_Indicators_Medium_Update.csv (UN interim update,
//          19 Jan 2026; its rows replace the original rows for the same location)
//          data/raw/un-wup-2025/WUP2025-F15-National-Definitions_percPop_by_category.xlsx (UN World
//          Urbanization Prospects 2025, percentage urban by national definition, 1950–2050) → `urbanPct`
// Output : src/data/wpp/world.json
//          src/data/wpp/countries/<ISO3>.json   one file per UN "country or area"
//          src/data/wpp/index.json              list of all countries or areas with current-year figures
//
// Units: UN gives people in thousands; we store whole people. Years up to 2023 are UN estimates,
// 2024 onwards are UN projections (medium variant) — every row carries `projection: true|false`.

import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const RAW = 'data/raw/un-wpp-2024';
const MAIN = 'WPP2024_Demographic_Indicators_Medium.csv.gz';
const UPDATE_ZIP = 'WPP2024_CSV_files_update.zip';
const UPDATE_CSV = 'WPP2024_Demographic_Indicators_Medium_Update.csv';
const OUT = 'src/data/wpp';
const CURRENT_YEAR = 2026;
const LAST_ESTIMATE_YEAR = 2023;

// ---------- CSV ----------
function parseCSV(text) {
  text = text.replace(/^﻿/, '');
  const rows = []; let row = []; let f = ''; let q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) {
      if (ch === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; }
      else f += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { row.push(f); f = ''; }
    else if (ch === '\n') { row.push(f.replace(/\r$/, '')); rows.push(row); row = []; f = ''; }
    else f += ch;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  const [head, ...body] = rows;
  return body.filter((r) => r.length === head.length).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}

const sha = (buf) => createHash('sha256').update(buf).digest('hex');
const mainBuf = readFileSync(join(RAW, MAIN));
const zipBuf = readFileSync(join(RAW, UPDATE_ZIP));
const mainRows = parseCSV(gunzipSync(mainBuf).toString('utf8'));
const updRows = parseCSV(execFileSync('unzip', ['-p', join(RAW, UPDATE_ZIP), UPDATE_CSV], { maxBuffer: 1 << 28 }).toString('utf8'));
const downloaded = (readFileSync(join(RAW, 'SOURCE.md'), 'utf8').match(/Downloaded \(UTC\): (\S+)/) || [])[1];

// ---------- UN WUP 2025: percentage urban by national definition (xlsx, read without extra packages) ----------
const WUP_DIR = 'data/raw/un-wup-2025';
const WUP_FILE = 'WUP2025-F15-National-Definitions_percPop_by_category.xlsx';
const unzipText = (zip, member) => execFileSync('unzip', ['-p', zip, member], { maxBuffer: 1 << 28 }).toString('utf8');
const xmlDecode = (s) => s.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'").replace(/&amp;/g, '&');
function readSheet(zip, sheetName) {
  const wbXml = unzipText(zip, 'xl/workbook.xml');
  const rid = (wbXml.match(new RegExp(`<sheet[^>]*name="${sheetName}"[^>]*r:id="([^"]+)"`)) || [])[1];
  const rels = unzipText(zip, 'xl/_rels/workbook.xml.rels');
  const target = (rels.match(new RegExp(`<Relationship[^>]*Id="${rid}"[^>]*Target="([^"]+)"`)) || rels.match(new RegExp(`<Relationship[^>]*Target="([^"]+)"[^>]*Id="${rid}"`)) || [])[1];
  if (!target) throw new Error(`Sheet ${sheetName} not found in ${zip}`);
  let shared = [];
  try {
    shared = [...unzipText(zip, 'xl/sharedStrings.xml').matchAll(/<si>([\s\S]*?)<\/si>/g)].map((m) => xmlDecode([...m[1].matchAll(/<t[^>]*>([\s\S]*?)<\/t>/g)].map((x) => x[1]).join('')));
  } catch { /* no shared strings */ }
  const xml = unzipText(zip, 'xl/' + target.replace(/^\/?xl\//, ''));
  const colIdx = (ref) => [...ref.replace(/\d+/g, '')].reduce((n, ch) => n * 26 + ch.charCodeAt(0) - 64, 0) - 1;
  return [...xml.matchAll(/<row[^>]*>([\s\S]*?)<\/row>/g)].map((rm) => {
    const row = [];
    for (const cm of rm[1].matchAll(/<c ([^>]*?)(?:\/>|>([\s\S]*?)<\/c>)/g)) {
      const ref = (cm[1].match(/r="([A-Z]+\d+)"/) || [])[1];
      const type = (cm[1].match(/t="([^"]+)"/) || [])[1];
      const v = ((cm[2] || '').match(/<v>([\s\S]*?)<\/v>/) || [])[1];
      const inline = ((cm[2] || '').match(/<t[^>]*>([\s\S]*?)<\/t>/) || [])[1];
      row[colIdx(ref)] = type === 's' ? shared[Number(v)] : type === 'inlineStr' ? xmlDecode(inline ?? '') : type === 'str' ? xmlDecode(v ?? '') : v == null ? null : Number(v);
    }
    return row;
  });
}
const wupZip = join(WUP_DIR, WUP_FILE);
const wupBuf = readFileSync(wupZip);
const wupRows = readSheet(wupZip, 'Urban');
const wupHead = wupRows[0].map((h) => (h == null ? '' : String(h)));
const wupLocCol = wupHead.indexOf('LocID');
const urbanByLoc = new Map(); // LocID → { year: pct }
for (const r of wupRows.slice(1)) {
  if (r[wupLocCol] == null) continue;
  const m = {};
  wupHead.forEach((h, i) => { if (/^\d{4}$/.test(h) && typeof r[i] === 'number') m[Number(h)] = r[i]; });
  urbanByLoc.set(String(r[wupLocCol]), m);
}
if (urbanByLoc.size < 230) throw new Error(`WUP file: only ${urbanByLoc.size} locations read`);
const wupDownloaded = (readFileSync(join(WUP_DIR, 'SOURCE.md'), 'utf8').match(/Downloaded \(UTC\): (\S+)/) || [])[1];

// Interim update replaces every row of the locations it contains.
const updatedLocs = new Set(updRows.map((r) => r.LocID));
const rows = [...mainRows.filter((r) => !updatedLocs.has(r.LocID)), ...updRows];

// ---------- helpers ----------
const num = (v) => (v === '' || v == null ? null : Number(v));
const people = (v) => (v === '' || v == null ? null : Math.round(Number(v) * 1000)); // thousands → people
const r2 = (v) => (v == null ? null : Math.round(v * 100) / 100);

function toYear(r) {
  const year = Number(r.Time);
  return {
    year,
    projection: year > LAST_ESTIMATE_YEAR,
    population: people(r.TPopulation1July),
    populationJan1: people(r.TPopulation1Jan),
    male: people(r.TPopulationMale1July),
    female: people(r.TPopulationFemale1July),
    densityPerKm2: num(r.PopDensity),
    growthRatePct: num(r.PopGrowthRate),
    change: people(r.PopChange),
    naturalChange: people(r.NatChange),
    births: people(r.Births),
    deaths: people(r.Deaths),
    netMigrants: people(r.NetMigrations),
    fertility: num(r.TFR),
    medianAge: num(r.MedianAgePop),
    lifeExpectancy: num(r.LEx),
    infantMortalityPer1000: num(r.IMR),
  };
}

// ---------- locations ----------
const locs = new Map(); // LocID → { meta, years[] }
for (const r of rows) {
  let l = locs.get(r.LocID);
  if (!l) locs.set(r.LocID, (l = { id: Number(r.LocID), name: r.Location, type: r.LocTypeName, parent: r.ParentID, iso3: r.ISO3_code, iso2: r.ISO2_code, years: [] }));
  l.years.push(toYear(r));
}
// Drop years without a mid-year population (the UN file ends with 1 January 2101 only).
for (const l of locs.values()) l.years = l.years.filter((y) => y.population != null).sort((a, b) => a.year - b.year);

const world = [...locs.values()].find((l) => l.type === 'World');
const countries = [...locs.values()].filter((l) => l.type === 'Country/Area');
if (!world || countries.length < 230) throw new Error(`Unexpected input: world=${!!world}, countries=${countries.length}`);

// Region chain: country → subregion → region (UN geographic groups)
// The UN file has no row for LocID 918 (Northern America), the parent of Bermuda, Canada, Greenland,
// Saint Pierre and Miquelon and the USA; we name it from the UN M49 classification.
const MISSING_GROUPS = { 918: { name: 'Northern America', type: 'Subregion', parent: null } };
const parentOf = (l) => locs.get(String(l.parent)) || MISSING_GROUPS[l.parent];
function regions(l) {
  const sub = parentOf(l);
  if (sub && sub.parent == null) return { subregion: sub.name, region: sub.name };
  const reg = sub && parentOf(sub);
  return { subregion: sub?.name ?? null, region: reg && reg.type !== 'World' ? reg.name : sub?.name ?? null };
}

// Rank and share of world, per year
const years = world.years.map((y) => y.year);
const rankByYear = new Map();
for (const yr of years) {
  const list = countries
    .map((c) => ({ c, p: c.years.find((y) => y.year === yr)?.population ?? -1 }))
    .sort((a, b) => b.p - a.p);
  const w = world.years.find((y) => y.year === yr).population;
  list.forEach(({ c, p }, i) => rankByYear.set(`${c.id}:${yr}`, { rank: i + 1, share: Math.round((p / w) * 1e6) / 1e4 /* 4 decimals: displayed values round once */ }));
}

const meta = {
  source: 'United Nations, Department of Economic and Social Affairs, Population Division (2024). World Population Prospects 2024, medium variant.',
  sourceUrl: 'https://population.un.org/wpp/',
  licence: 'CC BY 3.0 IGO',
  licenceUrl: 'https://creativecommons.org/licenses/by/3.0/igo/',
  files: [
    { file: MAIN, sha256: sha(mainBuf) },
    { file: UPDATE_ZIP, sha256: sha(zipBuf), note: `Interim update (19 Jan 2026) replaces rows for: ${[...updatedLocs].map((id) => locs.get(id).name).join(', ')}` },
  ],
  downloaded,
  urban: {
    source: 'United Nations, Department of Economic and Social Affairs, Population Division (2025). World Urbanization Prospects: The 2025 Revision, Online Edition. Percentage urban by national definition (F15).',
    sourceUrl: 'https://population.un.org/wup/',
    licence: 'CC BY 3.0 IGO',
    file: WUP_FILE,
    sha256: sha(wupBuf),
    downloaded: wupDownloaded,
    lastEstimateYear: 2025,
  },
  lastEstimateYear: LAST_ESTIMATE_YEAR,
  units: 'people (whole numbers); density people per km²; growthRatePct % per year; fertility births per woman; medianAge and lifeExpectancy years',
};

// ---------- write ----------
rmSync(OUT, { recursive: true, force: true });
mkdirSync(join(OUT, 'countries'), { recursive: true });
const write = (p, o) => writeFileSync(join(OUT, p), JSON.stringify(o) + '\n');

const urbanOf = (locId, year) => { const v = urbanByLoc.get(String(locId))?.[year]; return v == null ? null : v; };
write('world.json', { meta, name: 'World', years: world.years.map((y) => ({ ...y, urbanPct: urbanOf(world.id, y.year), worldRank: null, worldSharePct: 100 })) });

const index = [];
for (const c of countries) {
  const { subregion, region } = regions(c);
  const ys = c.years.map((y) => {
    const rk = rankByYear.get(`${c.id}:${y.year}`);
    return { ...y, urbanPct: urbanOf(c.id, y.year), worldRank: rk.rank, worldSharePct: rk.share };
  });
  // Land area implied by the UN's own population and density (km²), from the last estimate year.
  const base = ys.find((y) => y.year === LAST_ESTIMATE_YEAR);
  const landAreaKm2 = base?.densityPerKm2 ? Math.round(base.population / base.densityPerKm2) : null;
  const key = c.iso3 || `LOC${c.id}`;
  write(`countries/${key}.json`, { meta, unName: c.name, locId: c.id, iso3: c.iso3 || null, iso2: c.iso2 || null, region, subregion, landAreaKm2, years: ys });
  const cur = ys.find((y) => y.year === CURRENT_YEAR);
  index.push({ iso3: c.iso3 || null, iso2: c.iso2 || null, locId: c.id, unName: c.name, region, subregion, file: `countries/${key}.json`, population: cur.population, worldRank: cur.worldRank, worldSharePct: cur.worldSharePct, densityPerKm2: cur.densityPerKm2 });
}
index.sort((a, b) => a.worldRank - b.worldRank);
write('index.json', { meta, year: CURRENT_YEAR, worldPopulation: world.years.find((y) => y.year === CURRENT_YEAR).population, countries: index });

const noUrban = countries.filter((c) => !urbanByLoc.has(String(c.id))).map((c) => c.name);
if (noUrban.length) console.warn(`! No WUP urban share for: ${noUrban.join(', ')}`);
console.log(`✓ ${countries.length} countries or areas + World, ${years[0]}–${years.at(-1)}. Interim update applied to: ${[...updatedLocs].map((id) => locs.get(id).name).join(', ')}.`);
