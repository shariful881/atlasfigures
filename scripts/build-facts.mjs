// build-facts (task 156): fixed facts for every country or area in src/data/country-list.json, from the original
// files in data/raw/facts/ (fetched by .github/workflows/fetch-facts.yml; licences in its SOURCE.md):
//   currency, official languages ............ Unicode CLDR (Unicode License v3)
//   calling code, internet domain, land neighbours ... GeoNames (CC BY 4.0)
//   time zones ............................... IANA time zone database (public domain); UTC offsets for 2026 from Node's ICU
//   landlocked, highest point, driving side, plug types, emergency numbers ... Wikidata (CC0)
// Where a second source holds the same fact (GeoNames for currency; Wikidata for calling code, domain, official languages and land borders),
// the two are compared and the result is kept in `checks` ("agree" / "differ" with both values). A fact whose sources
// differ is NOT used as a live figure: profiles show it as "to check" until it has been checked by hand.
// (Wikidata's "shares border with" also lists sea borders, so a GeoNames land neighbour only has to appear there.)
// Output (generated, git-ignored): src/data/facts/index.json. Runs in `npm run data` and before every build.
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const RAW = 'data/raw/facts';
const OUT = 'src/data/facts';
export const YEAR = 2026;

const read = (f) => readFileSync(`${RAW}/${f}`, 'utf8');
const json = (f) => JSON.parse(read(f));
const sha = (f) => createHash('sha256').update(readFileSync(`${RAW}/${f}`)).digest('hex');
const qid = (u) => (u || '').replace('http://www.wikidata.org/entity/', '');

export function loadFacts() {
  const source = read('SOURCE.md');
  // every file must match the SHA-256 recorded when it was downloaded
  for (const m of source.matchAll(/^\| [^|]+ \| (\S+) \| [^|]+ \| [^|]+ \| \d+ \| ([0-9a-f]{64}) \|$/gm)) {
    if (sha(m[1]) !== m[2]) throw new Error(`${RAW}/${m[1]}: SHA-256 does not match SOURCE.md`);
  }
  const list = JSON.parse(readFileSync('src/data/country-list.json', 'utf8')).countries;
  const byIso2 = Object.fromEntries(list.map((c) => [c.iso2, c.iso3]));

  // ---------- CLDR ----------
  const cd = json('cldr-currencyData.json').supplemental.currencyData.region;
  const cn = json('cldr-currencies.json').main.en.numbers.currencies;
  const ti = json('cldr-territoryInfo.json').supplemental.territoryInfo;
  const ln = json('cldr-languages.json').main.en.localeDisplayNames.languages;
  const currencies = (iso2) => (cd[iso2] ?? []).flatMap((o) => Object.entries(o))
    .filter(([, v]) => !v._to && v._tender !== 'false')
    .map(([code]) => ({ code, name: cn[code]?.displayName ?? code, symbol: cn[code]?.['symbol-alt-narrow'] ?? cn[code]?.symbol ?? code }));
  const languages = (iso2) => Object.entries(ti[iso2]?.languagePopulation ?? {})
    .filter(([, v]) => v._officialStatus === 'official') // national official status only (not de facto, not regional)
    .sort((a, b) => Number(b[1]._populationPercent) - Number(a[1]._populationPercent) || a[0].localeCompare(b[0]))
    .map(([code, v]) => ({ code, name: ln[code] ?? ln[code.split('_')[0]] ?? code, status: v._officialStatus }));

  // ---------- GeoNames ----------
  const gi = {};
  for (const l of read('geonames-countryInfo.txt').split('\n')) {
    if (!l || l.startsWith('#')) continue;
    const f = l.split('\t');
    gi[f[0]] = { iso3: f[1], tld: f[9] || null, currency: f[10] || null, phone: f[12] || null, neighbours: (f[17] || '').split(',').filter(Boolean) };
  }
  // ---------- IANA tz ----------
  const zones = {};
  for (const l of read('tz-zone1970.tab').split('\n')) {
    if (!l || l.startsWith('#')) continue;
    const [ccs, , zone] = l.split('\t');
    for (const cc of ccs.split(',')) (zones[cc] ??= []).push(zone);
  }
  const offset = (zone, month) => new Intl.DateTimeFormat('en-US', { timeZone: zone, timeZoneName: 'longOffset' })
    .formatToParts(new Date(Date.UTC(YEAR, month, 15, 12))).find((p) => p.type === 'timeZoneName').value.replace('GMT', 'UTC').replace(/^UTC$/, 'UTC+00:00');

  // ---------- Wikidata ----------
  const items = {};
  for (const r of json('wikidata/items.json')) {
    const best = items[r.iso3];
    if (!best || Number(r.sitelinks) > best.sitelinks || (Number(r.sitelinks) === best.sitelinks && qid(r.item) < best.qid)) items[r.iso3] = { qid: qid(r.item), label: r.itemLabel, sitelinks: Number(r.sitelinks) };
  }
  const wd = (name) => {
    const out = {};
    for (const r of json(`wikidata/${name}.json`)) if (items[r.iso3]?.qid === qid(r.item)) (out[r.iso3] ??= []).push(r);
    return out;
  };
  const W = Object.fromEntries(['calling', 'tld', 'languages', 'borders', 'highest', 'driving', 'plugs', 'emergency', 'landlocked'].map((n) => [n, wd(n)]));
  // Wikidata plug items → IEC 60083 letter types (the generic "British and related types" article is not a type and is left out)
  const PLUG = { Q1528507: 'G' };
  const PLUG_BY_LABEL = { 'NEMA 1-15': 'A', 'NEMA 5-15': 'B', Europlug: 'C', 'BS 546': 'D', 'Type E': 'E', Schuko: 'F', 'BS 1363': 'G', 'Type H': 'H', 'AS/NZS 3112': 'I', 'SN 441011': 'J', 'Type K': 'K', 'Type L': 'L', 'IEC 60906-1': 'N' };

  // the same language under another English name in CLDR and Wikidata (only spelling variants — no merging of languages)
  const ALIAS = { slovene: 'slovenian', maldivian: 'divehi', swazi: 'swati', greenlandic: 'kalaallisut', sesotho: 'southern sotho', 'standard chinese': 'chinese', putonghua: 'chinese', 'standard taiwanese mandarin': 'chinese', chewa: 'nyanja', 'modern standard arabic': 'arabic', 'standard arabic': 'arabic', 'mandarin chinese': 'chinese' };
  const alias = (s) => { const x = s.toLowerCase(); return ALIAS[x] ?? x; };
  const norm = (s) => (s || '').replace(/[\s-]/g, '');
  const uniq = (a) => [...new Set(a)];
  const facts = {};
  for (const c of list) {
    const g = gi[c.iso2];
    const f = { iso3: c.iso3, iso2: c.iso2, wikidata: items[c.iso3]?.qid ?? null, checks: {} };
    // currency
    f.currencies = currencies(c.iso2);
    if (f.currencies.length && g?.currency) f.checks.currency = f.currencies.some((x) => x.code === g.currency) ? 'agree' : { differ: { cldr: f.currencies.map((x) => x.code), geonames: [g.currency] } };
    // official languages
    f.languages = languages(c.iso2);
    const wl = uniq((W.languages[c.iso3] ?? []).map((r) => r.valueLabel));
    if (f.languages.length && wl.length) {
      const a = f.languages.map((l) => alias(l.name)); const b = wl.map(alias);
      f.checks.languages = a.every((x) => b.some((y) => y.includes(x) || x.includes(y))) ? 'agree' : { differ: { cldr: f.languages.map((l) => l.name), wikidata: wl } };
    }
    // calling code (GeoNames; Wikidata cross-check)
    f.callingCode = g?.phone ? g.phone.split(/\s*and\s*|,\s*/).map((p) => `+${p.replace(/^\+/, '')}`) : [];
    const wc = uniq((W.calling[c.iso3] ?? []).map((r) => `+${r.value.replace(/^\+/, '').trim()}`));
    if (f.callingCode.length && wc.length) f.checks.callingCode = f.callingCode.some((x) => wc.some((y) => norm(y).startsWith(norm(x)) || norm(x).startsWith(norm(y)))) ? 'agree' : { differ: { geonames: f.callingCode, wikidata: wc } };
    // internet domain
    f.tld = g?.tld || null;
    const wt = uniq((W.tld[c.iso3] ?? []).map((r) => r.valueLabel).filter((x) => x && !/^Q\d+$/.test(x)));
    if (f.tld && wt.length) f.checks.tld = wt.includes(f.tld) ? 'agree' : { differ: { geonames: f.tld, wikidata: wt } };
    // neighbours (land borders)
    f.neighbours = (g?.neighbours ?? []).map((x) => byIso2[x]).filter(Boolean).sort();
    const wb = uniq((W.borders[c.iso3] ?? []).map((r) => r.value)).filter((x) => list.some((l) => l.iso3 === x)).sort();
    if (f.neighbours.length || wb.length) {
      const extra = f.neighbours.filter((x) => !wb.includes(x));
      f.checks.neighbours = !extra.length ? 'agree' : { differ: { geonames: f.neighbours, wikidata: wb } };
    }
    // landlocked (Wikidata only; shown only for places Wikidata lists, plus "no" where GeoNames gives the place a neighbour-free or coastal status is unknown)
    f.landlocked = W.landlocked[c.iso3] ? true : null;
    // highest point
    const hpAll = W.highest[c.iso3] ?? [];
    const hp = [...new Map(hpAll.map((h) => [h.valueLabel, { ...h }])).values()]; // the same peak can sit on two items with one label
    const hpM = uniq(hpAll.map((h) => h.metres).filter((m) => m != null).map((m) => Math.round(Number(m))));
    if (hp.length === 1 && hpM.length === 1) hp[0].metres = hpM[0]; else if (hp.length === 1) hp[0].metres = null;
    f.highestPoint = hp.length === 1 && hp[0].valueLabel && !/^Q\d+$/.test(hp[0].valueLabel) ? { name: hp[0].valueLabel, metres: hp[0].metres != null ? Math.round(Number(hp[0].metres)) : null, wikidata: qid(hp[0].value) } : null;
    // two different peaks → to check; one peak with several published heights → name only, no height
    if (hp.length > 1) f.checks.highestPoint = { differ: { wikidata: hpAll.map((h) => `${h.valueLabel} ${h.metres ?? ''}`.trim()) } };
    if (f.highestPoint && hpM.length > 1) f.highestPoint.heightsDiffer = hpM.sort((a, b) => a - b);
    // driving side
    const ds = uniq((W.driving[c.iso3] ?? []).map((r) => r.valueLabel));
    f.drivingSide = ds.length === 1 ? ds[0] : null;
    if (ds.length > 1) f.checks.drivingSide = { differ: { wikidata: ds } };
    // plug types
    f.plugs = uniq((W.plugs[c.iso3] ?? []).map((r) => PLUG[qid(r.value)] ?? PLUG_BY_LABEL[r.valueLabel]).filter(Boolean)).sort();
    // emergency numbers
    f.emergency = uniq((W.emergency[c.iso3] ?? []).map((r) => r.valueLabel).filter((x) => /^[0-9]{2,4}$/.test(x))).sort((a, b) => a.length - b.length || a.localeCompare(b));
    // time zones
    f.timeZones = (zones[c.iso2] ?? []).map((z) => ({ zone: z, january: offset(z, 0), july: offset(z, 6) }));
    facts[c.iso3] = f;
  }
  // hand checks where the sources differ (data/facts-checked.json)
  const hand = JSON.parse(readFileSync('data/facts-checked.json', 'utf8')).checks;
  for (const h of hand) {
    const f = facts[h.iso3]; const chk = f?.checks[h.fact];
    if (!chk || chk === 'agree' || JSON.stringify(chk.differ) !== JSON.stringify(h.whenDiffer)) continue; // sources changed → back to "to check"
    for (const [k, v] of Object.entries(h.set)) f[k] = k === 'currencies' ? v.map((x) => f.currencies.find((y) => y.code === x.code) ?? x) : v;
    f.checks[h.fact] = { checked: { on: h.checkedOn, by: h.checkedBy, against: h.against, url: h.url }, differ: chk.differ };
  }
  return { facts, versions: { cldr: (source.match(/Unicode CLDR (\S+) —/) || [])[1], tz: (source.match(/IANA time zone database (\S+) —/) || [])[1], icuTz: process.versions.tz, downloaded: (source.match(/Downloaded \(UTC\): (\S+)/) || [])[1] } };
}

// one-line display text per fact (profiles and later the Key facts card read these)
export function factText(f, key, names) {
  const nm = (iso3) => names[iso3] ?? iso3;
  switch (key) {
    case 'currency': return f.currencies.length ? f.currencies.map((x) => `${x.name} (${x.code}${x.symbol && x.symbol !== x.code ? `, ${x.symbol}` : ''})`).join('; ') : null;
    case 'languages': return f.languages.length ? f.languages.map((l) => l.name).join(', ') : null;
    case 'callingCode': return f.callingCode.length ? f.callingCode.join(', ') : null;
    case 'tld': return f.tld;
    case 'timeZones': {
      if (!f.timeZones.length) return null;
      const offs = [...new Set(f.timeZones.map((z) => (z.january === z.july ? z.january : `${z.january}/${z.july.replace('UTC', '')}`)))];
      return `${offs.join(', ')}${f.timeZones.length > 1 ? ` (${f.timeZones.length} zones)` : ''}`;
    }
    case 'neighbours': return f.neighbours.length ? f.neighbours.map(nm).join(', ') : 'None (no land borders)';
    case 'landlocked': return f.landlocked ? 'Yes' : null;
    case 'highestPoint': return f.highestPoint ? `${f.highestPoint.name}${f.highestPoint.metres != null ? `, ${f.highestPoint.metres.toLocaleString('en-US')} m` : ''}` : null;
    case 'drivingSide': return f.drivingSide ? `${f.drivingSide[0].toUpperCase()}${f.drivingSide.slice(1)}` : null;
    case 'plugs': return f.plugs.length ? `Type ${f.plugs.join(', ')}` : null;
    case 'emergency': return f.emergency.length ? f.emergency.join(', ') : null;
    default: throw new Error(`unknown fact ${key}`);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  if (!existsSync(`${RAW}/SOURCE.md`)) throw new Error(`Missing ${RAW} — run the "Fetch country facts (dev-data)" workflow`);
  const { facts, versions } = loadFacts();
  mkdirSync(OUT, { recursive: true });
  writeFileSync(`${OUT}/index.json`, JSON.stringify({ versions, facts }) + '\n');
  const all = Object.values(facts);
  const differ = all.flatMap((f) => Object.entries(f.checks).filter(([, v]) => v !== 'agree').map(([k]) => `${f.iso3}.${k}`));
  const has = (k) => all.filter((f) => (Array.isArray(f[k]) ? f[k].length : f[k] != null)).length;
  console.log(`✓ facts: ${all.length} countries or areas — currency ${has('currencies')}, languages ${has('languages')}, calling code ${has('callingCode')}, domain ${has('tld')}, time zones ${has('timeZones')}, highest point ${has('highestPoint')}, driving side ${has('drivingSide')}, plugs ${has('plugs')}, emergency ${has('emergency')}; ${differ.length} facts where the second source differs (check-facts lists them).`);
}

// Hand checks of single-source Wikidata facts recorded on country pages (task 172): src/data/country-pages/<slug>.json
// `factChecks` entries with `wikidata` (the Wikidata text when it was checked) and `value` (what the cited source says,
// shown on the page). The checked value is used only while Wikidata still says what it said at the check; if Wikidata
// changes, the fact goes back to "to check" (and check-country-pages fails until it is checked again).
export function pageFactChecks(dir = 'src/data/country-pages') {
  const out = {};
  if (!existsSync(dir)) return out;
  for (const f of readdirSync(dir).filter((x) => x.endsWith('.json'))) {
    const pg = JSON.parse(readFileSync(`${dir}/${f}`, 'utf8'));
    for (const id of pg.checkedFacts ?? []) {
      const chk = (pg.factChecks ?? []).find((x) => x.fact === id);
      if (chk) (out[pg.iso3] ??= {})[id] = chk;
    }
  }
  return out;
}
/** Applies a page hand check to a Wikidata fact text: { value, source } when it applies, { stale } when Wikidata changed. */
export function applyHandCheck(chk, wikidataText) {
  if (!chk || wikidataText == null) return null;
  if (chk.wikidata != null && chk.wikidata !== wikidataText) return { stale: true };
  return { value: chk.value, source: `${chk.sourceName} (checked by hand ${chk.checkedOn})` };
}
