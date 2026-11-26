// Turns the original energy and CO2 files in data/raw/energy/ (fetched by .github/workflows/fetch-energy.yml)
// into src/data/energy/index.json for the energy pages (task 110). Generated, git-ignored, never edited by hand.
//  - Global Carbon Project fossil CO2 dataset (GCB*_MtCO2_flat.csv): Total (MtCO2) and Per Capita (tCO2), by year.
//  - Ember Yearly Electricity Data (global CSV): Total generation (TWh), Renewables and Wind and solar
//    (TWh and share of generation, %), Fossil share, by year, for "Country or economy" rows.
// Values are kept exactly as published (numbers parsed from the CSV text). scripts/check-energy.mjs compares
// every generated value back against the original files.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const RAW = 'data/raw/energy';
const OUT = 'src/data/energy';
const csv = (text) => {
  const rows = []; let row = [], f = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true; else if (c === ',') { row.push(f); f = ''; } else if (c === '\n') { row.push(f); rows.push(row); row = []; f = ''; } else if (c !== '\r') f += c;
  }
  if (f || row.length) { row.push(f); rows.push(row); }
  const head = rows.shift();
  return rows.filter((r) => r.length === head.length).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
};
const num = (s) => (s === '' || s == null ? null : Number(s));

if (!existsSync(RAW)) { console.log('build-energy: no data/raw/energy yet, skipped'); process.exit(0); }
const files = readdirSync(RAW);
const gcbFile = files.find((f) => /_MtCO2_flat\.csv$/.test(f));
const gcbVersion = gcbFile.replace('_MtCO2_flat.csv', '');
const rec = JSON.parse(readFileSync(join(RAW, 'gcb-zenodo-record.json'), 'utf8'));
const source = readFileSync(join(RAW, 'SOURCE.md'), 'utf8');
const downloaded = source.match(/Downloaded \(UTC\): (\S+)/)[1];

// Regions for the table filter: World Bank region where the economy is in WDI, otherwise none.
const wdiRegion = new Map();
if (existsSync('src/data/wdi/countries')) for (const f of readdirSync('src/data/wdi/countries')) {
  const d = JSON.parse(readFileSync(join('src/data/wdi/countries', f), 'utf8')); wdiRegion.set(d.iso3, d.region);
}

const countries = {};
const get = (iso3, name) => (countries[iso3] ??= { iso3, sourceName: name, region: wdiRegion.get(iso3) ?? null, series: {} });
const push = (o, k, y, v) => { if (v == null || Number.isNaN(v)) return; (o.series[k] ??= []).push([y, v]); };
let world = { series: {} };

// Global Carbon Project. ISO codes starting with X are bunkers/aggregates (XIS shipping, XIA aviation), except Kosovo.
for (const r of csv(readFileSync(join(RAW, gcbFile), 'utf8'))) {
  const iso = r['ISO 3166-1 alpha-3'], y = Number(r.Year);
  if (iso === 'WLD') { push(world, 'co2', y, num(r.Total)); push(world, 'co2pc', y, num(r['Per Capita'])); continue; }
  if (!iso || (iso.startsWith('X') && iso !== 'XKX')) continue;
  const o = get(iso === 'KSV' ? 'XKX' : iso, r.Country); // GCB codes Kosovo KSV; the UN and Ember use XKX
  push(o, 'co2', y, num(r.Total));
  if (num(r['Per Capita'])) push(o, 'co2pc', y, num(r['Per Capita']));
}

// Ember.
const EMBER = { 'Total generation': ['gen', null], Renewables: ['ren', 'renShare'], 'Wind and solar': ['ws', 'wsShare'], Fossil: [null, 'fossilShare'], Hydro: [null, 'hydroShare'], 'Other renewables': [null, 'otherRenShare'] };
for (const r of csv(readFileSync(join(RAW, 'ember-yearly-electricity-global.csv'), 'utf8'))) {
  const m = EMBER[r['Electricity source']]; if (!m) continue;
  const y = Number(r.Year);
  const target = r['Area type'] === 'Country or economy' && r['ISO 3 code'] ? get(r['ISO 3 code'], r.Area) : r.Area === 'World' ? world : null;
  if (!target) continue;
  if (m[0]) push(target, m[0], y, num(r['Generation (TWh)']));
  if (m[1]) push(target, m[1], y, num(r['Share of generation (%)']));
  if (target !== world && !target.emberName) target.emberName = r.Area;
}
// Keep the UN WPP list of countries and areas only (data guide §5); drops e.g. Antarctica and Christmas Island.
const unList = new Set(JSON.parse(readFileSync('src/data/wpp/index.json', 'utf8')).countries.map((c) => c.iso3));
const dropped = Object.keys(countries).filter((k) => !unList.has(k));
for (const k of dropped) delete countries[k];
for (const o of [...Object.values(countries), world]) for (const k in o.series) o.series[k].sort((a, b) => a[0] - b[0]);

const meta = {
  gcb: { name: 'Global Carbon Project, fossil CO2 emissions dataset', version: rec.metadata.version, file: gcbFile, published: rec.metadata.publication_date, doi: rec.doi, url: `https://doi.org/${rec.doi}`, licence: 'CC BY 4.0', licenceUrl: 'https://creativecommons.org/licenses/by/4.0/', budget: gcbVersion.replace(/^GCB(\d{4}).*/, 'Global Carbon Budget $1') },
  ember: { name: 'Ember, Yearly Electricity Data', url: 'https://ember-energy.org/data/yearly-electricity-data/', file: 'ember-yearly-electricity-global.csv', licence: 'CC BY 4.0', licenceUrl: 'https://creativecommons.org/licenses/by/4.0/' },
  downloaded,
};
mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, 'index.json'), JSON.stringify({ meta, world, countries }));
console.log(`✓ Energy: ${Object.keys(countries).length} countries or areas (not in the UN list, left out: ${dropped.join(', ')}) (${meta.gcb.version} CO2, Ember electricity), downloaded ${downloaded}.`);
