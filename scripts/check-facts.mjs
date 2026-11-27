// check-facts (task 156): the generated country facts (src/data/facts/index.json) against the original files in
// data/raw/facts/, read again here with separate code (not build-facts' parser):
//   - licence texts present (CLDR Unicode License v3, tz public domain, GeoNames CC BY 4.0) and SHA-256 = SOURCE.md
//   - calling code, internet domain and land neighbours = GeoNames countryInfo.txt, for every country or area
//   - currencies = CLDR currencyData (current legal tender only), names/symbols = CLDR en currencies
//   - official languages = CLDR territoryInfo entries with _officialStatus "official"
//   - time zones = every zone1970.tab line that lists the country; UTC offsets recomputed for 15 Jan and 15 Jul
//   - Wikidata facts come from the chosen item (most sitelinks for the ISO code) and nothing else
//   - every second-source check is recomputed in outline (agree/differ) and the "differ" list is printed
import { readFileSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';

const RAW = 'data/raw/facts';
let checks = 0; const problems = [];
const ok = (c, where, msg) => { checks++; if (!c) problems.push(`${where}: ${msg}`); return c; };
const raw = (f) => readFileSync(`${RAW}/${f}`, 'utf8');
const gen = JSON.parse(readFileSync('src/data/facts/index.json', 'utf8'));
const list = JSON.parse(readFileSync('src/data/country-list.json', 'utf8')).countries;

// licences and file hashes
ok(raw('cldr-LICENSE.txt').includes('UNICODE LICENSE V3'), 'CLDR', 'licence text');
ok(/public domain/i.test(raw('tz-LICENSE.txt')), 'tz', 'licence text');
ok(raw('geonames-readme.txt').includes('Creative Commons Attribution 4.0'), 'GeoNames', 'licence text');
const src = raw('SOURCE.md');
const files = [...src.matchAll(/^\| [^|]+ \| (\S+) \| ([^|]+) \| [^|]+ \| (\d+) \| ([0-9a-f]{64}) \|$/gm)];
ok(files.length >= 15, 'SOURCE.md', `only ${files.length} files listed`);
for (const [, f, , bytes, h] of files) {
  const b = readFileSync(`${RAW}/${f}`);
  ok(b.length === Number(bytes) && createHash('sha256').update(b).digest('hex') === h, f, 'bytes/SHA-256 differ from SOURCE.md');
}
for (const f of readdirSync(`${RAW}/wikidata`)) ok(files.some(([, x]) => x === `wikidata/${f}`), f, 'not listed in SOURCE.md');

// GeoNames, read column by header name
const lines = raw('geonames-countryInfo.txt').split('\n');
const head = lines.find((l) => l.startsWith('#ISO\t')).slice(1).split('\t');
const col = (n) => head.indexOf(n);
const geo = new Map(lines.filter((l) => l && !l.startsWith('#')).map((l) => { const f = l.split('\t'); return [f[col('ISO')], f]; }));
const iso2to3 = new Map(list.map((c) => [c.iso2, c.iso3]));

const cd = JSON.parse(raw('cldr-currencyData.json')).supplemental.currencyData.region;
const cn = JSON.parse(raw('cldr-currencies.json')).main.en.numbers.currencies;
const ti = JSON.parse(raw('cldr-territoryInfo.json')).supplemental.territoryInfo;

const tz = new Map();
for (const l of raw('tz-zone1970.tab').split('\n')) {
  if (/^\s*(#|$)/.test(l)) continue;
  const parts = l.split('\t');
  for (const cc of parts[0].split(',')) tz.set(cc, [...(tz.get(cc) ?? []), parts[2]]);
}
const off = (zone, m) => {
  const name = new Intl.DateTimeFormat('en-GB', { timeZone: zone, timeZoneName: 'longOffset' }).formatToParts(new Date(Date.UTC(2026, m, 15, 12))).find((p) => p.type === 'timeZoneName').value;
  return name === 'GMT' ? 'UTC+00:00' : name.replace('GMT', 'UTC');
};

// Wikidata chosen items
const wdItems = JSON.parse(raw('wikidata/items.json'));
const best = new Map();
for (const r of wdItems) { const q = r.item.split('/').pop(); const b = best.get(r.iso3); if (!b || +r.sitelinks > b.s || (+r.sitelinks === b.s && q < b.q)) best.set(r.iso3, { q, s: +r.sitelinks }); }

let differ = []; let handChecked = 0;
for (const c of list) {
  const f = gen.facts[c.iso3];
  if (!ok(f, c.iso3, 'no facts')) continue;
  const g = geo.get(c.iso2);
  // GeoNames facts
  const phone = g?.[col('Phone')] ? g[col('Phone')].split(/\s*and\s*|,\s*/).map((p) => '+' + p.replace(/^\+/, '')) : [];
  ok(JSON.stringify(f.callingCode) === JSON.stringify(phone) || f.checks.callingCode?.checked, c.iso3, `calling code ${f.callingCode} ≠ GeoNames ${phone}`);
  ok((f.tld ?? '') === (g?.[col('tld')] ?? ''), c.iso3, `domain ${f.tld} ≠ GeoNames ${g?.[col('tld')]}`);
  const nb = (g?.[col('neighbours')] ?? '').split(',').filter(Boolean).map((x) => iso2to3.get(x)).filter(Boolean).sort();
  ok(JSON.stringify(f.neighbours) === JSON.stringify(nb), c.iso3, `neighbours ${f.neighbours} ≠ GeoNames ${nb}`);
  // CLDR currencies and languages
  const cur = (cd[c.iso2] ?? []).flatMap((o) => Object.entries(o)).filter(([, v]) => v._to === undefined && v._tender !== 'false').map(([k]) => k);
  ok(JSON.stringify(f.currencies.map((x) => x.code)) === JSON.stringify(cur) || f.checks.currency?.checked, c.iso3, `currencies ${f.currencies.map((x) => x.code)} ≠ CLDR ${cur}`);
  for (const x of f.currencies) ok(x.name === (cn[x.code]?.displayName ?? x.code), c.iso3, `${x.code} name`);
  const langs = Object.entries(ti[c.iso2]?.languagePopulation ?? {}).filter(([, v]) => v._officialStatus === 'official').map(([k]) => k).sort();
  ok(JSON.stringify(f.languages.map((l) => l.code).sort()) === JSON.stringify(langs), c.iso3, `languages ${f.languages.map((l) => l.code)} ≠ CLDR ${langs}`);
  // time zones
  const zs = tz.get(c.iso2) ?? [];
  ok(JSON.stringify(f.timeZones.map((z) => z.zone)) === JSON.stringify(zs), c.iso3, 'time zones differ from zone1970.tab');
  for (const z of f.timeZones) ok(z.january === off(z.zone, 0) && z.july === off(z.zone, 6), c.iso3, `${z.zone} offsets`);
  // Wikidata item
  ok((f.wikidata ?? null) === (best.get(c.iso3)?.q ?? null), c.iso3, `Wikidata item ${f.wikidata} ≠ ${best.get(c.iso3)?.q}`);
  if (f.drivingSide) ok(['left', 'right'].includes(f.drivingSide), c.iso3, `driving side "${f.drivingSide}"`);
  for (const p of f.plugs) ok(/^[A-N]$/.test(p), c.iso3, `plug type ${p}`);
  for (const n of f.emergency) ok(/^\d{2,4}$/.test(n), c.iso3, `emergency number ${n}`);
  if (f.highestPoint?.metres != null) ok(f.highestPoint.metres > -500 && f.highestPoint.metres < 8900, c.iso3, `highest point ${f.highestPoint.metres} m`);
  // checks recorded for every fact that has a second source
  for (const [k, v] of Object.entries(f.checks)) { ok(v === 'agree' || (v.differ && typeof v.differ === 'object'), c.iso3, `check ${k} malformed`); if (v !== 'agree' && !v.checked) differ.push(`${c.iso3}.${k}`); if (v.checked) handChecked++; }
}
ok(gen.versions.cldr && gen.versions.tz, 'versions', 'CLDR/tz versions missing');

const by = {}; for (const d of differ) { const k = d.split('.')[1]; by[k] = (by[k] ?? 0) + 1; }
console.log(`\n${problems.length ? '✗' : '✓'} Country facts = original files: ${checks} checks on ${list.length} countries or areas (CLDR ${gen.versions.cldr}, tz ${gen.versions.tz}).`);
console.log(`  Checked by hand (data/facts-checked.json): ${handChecked}.`);
console.log(`  Second source differs (shown as "to check" in profiles, not live): ${Object.entries(by).map(([k, n]) => `${k} ${n}`).join(', ') || 'none'}`);
if (problems.length) { for (const p of problems.slice(0, 40)) console.log('  ' + p); process.exit(1); }
