// Builds AtlasFigures' generated economy data from the ORIGINAL World Bank files in data/raw/wdi/.
// Run: npm run data          (runs after build-data.mjs; never edit the output by hand; re-run this instead)
//
// Input  : data/raw/wdi/<CODE>.zip            World Bank bulk CSV (API_<CODE>_…csv + Metadata_Country_… +
//                                             Metadata_Indicator_…), one per indicator in data/wdi-indicators.txt
//          data/raw/wdi/<CODE>.metadata.json  World Bank API series metadata (licence, source)
//          data/raw/wdi/SOURCE.md             download time, URLs, SHA-256 (written by fetch-wdi.yml)
// Output : src/data/wdi/meta.json             indicators: name, unit, source, licence, WDI last-updated date, file hash
//          src/data/wdi/countries/<ISO3>.json one file per World Bank economy (not aggregates)
//          src/data/wdi/aggregates.json       World, regions and income groups (World Bank aggregates)
//          src/data/wdi/index.json            every economy with its latest value of every indicator
//
// Values are copied exactly as the World Bank publishes them (full precision); only empty cells are dropped.
// Rounding happens on the page (src/lib/econ.ts), never here.

import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { join } from 'node:path';

const RAW = 'data/raw/wdi';
const OUT = 'src/data/wdi';
const LIST = 'data/wdi-indicators.txt';

// Short labels and units used on the site (the World Bank's own name is kept too).
export const LABELS = {
  'NY.GDP.MKTP.CD': { key: 'gdp', label: 'GDP', unit: 'current US$' },
  'NY.GDP.PCAP.CD': { key: 'gdpPerCapita', label: 'GDP per person', unit: 'current US$' },
  'NY.GDP.PCAP.PP.CD': { key: 'gdpPerCapitaPpp', label: 'GDP per person, PPP', unit: 'current international $' },
  'NY.GDP.MKTP.KD.ZG': { key: 'gdpGrowthPct', label: 'GDP growth', unit: '% per year (constant prices)' },
  'FP.CPI.TOTL.ZG': { key: 'inflationPct', label: 'Inflation (consumer prices)', unit: '% per year' },
  'SL.UEM.TOTL.ZS': { key: 'unemploymentPct', label: 'Unemployment', unit: '% of labour force (modelled ILO estimate)' },
  'BX.TRF.PWKR.CD.DT': { key: 'remittances', label: 'Remittances received', unit: 'current US$' },
  'BX.TRF.PWKR.DT.GD.ZS': { key: 'remittancesPctGdp', label: 'Remittances received', unit: '% of GDP' },
  'IT.NET.USER.ZS': { key: 'internetPct', label: 'Internet users', unit: '% of population' },
  'IT.CEL.SETS.P2': { key: 'mobilePer100', label: 'Mobile subscriptions', unit: 'per 100 people' },
  'IT.CEL.SETS': { key: 'mobileSubs', label: 'Mobile subscriptions', unit: 'subscriptions' },
  'IT.NET.BBND.P2': { key: 'broadbandPer100', label: 'Fixed broadband subscriptions', unit: 'per 100 people' },
  'SH.DYN.MORT': { key: 'under5Mortality', label: 'Under-5 mortality', unit: 'deaths per 1,000 live births' },
  'SP.DYN.IMRT.IN': { key: 'infantMortality', label: 'Infant mortality', unit: 'deaths per 1,000 live births' },
  'NE.EXP.GNFS.CD': { key: 'exports', label: 'Exports of goods and services', unit: 'current US$' },
  'NE.IMP.GNFS.CD': { key: 'imports', label: 'Imports of goods and services', unit: 'current US$' },
  'NE.EXP.GNFS.ZS': { key: 'exportsPctGdp', label: 'Exports of goods and services', unit: '% of GDP' },
  'NE.IMP.GNFS.ZS': { key: 'importsPctGdp', label: 'Imports of goods and services', unit: '% of GDP' },
  'SH.STA.MMRT': { key: 'maternalMortality', label: 'Maternal mortality ratio', unit: 'deaths per 100,000 live births (modelled estimate)' },
  'AG.LND.TOTL.K2': { key: 'landArea', label: 'Land area', unit: 'sq. km' },
  'AG.LND.FRST.ZS': { key: 'forestPct', label: 'Forest area', unit: '% of land area' },
  'AG.LND.FRST.K2': { key: 'forestArea', label: 'Forest area', unit: 'sq. km' },
};

// ---------- CSV (same parser rules as build-data.mjs) ----------
export function parseCSVRows(text) {
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
  return rows;
}
const toObjects = (rows) => {
  const [head, ...body] = rows;
  return body.filter((r) => r.length >= head.length).map((r) => Object.fromEntries(head.map((h, i) => [h, r[i]])));
};
const members = (zip) => execFileSync('unzip', ['-Z1', zip]).toString('utf8').split('\n').filter(Boolean);
const unzipText = (zip, member) => execFileSync('unzip', ['-p', zip, member], { maxBuffer: 1 << 28 }).toString('utf8');
const sha = (buf) => createHash('sha256').update(buf).digest('hex');

/** Reads one World Bank bulk zip: { lastUpdated, years, rows: [{code, name, values: {year: number}}], countryMeta } */
export function readWdiZip(zip, code) {
  const names = members(zip);
  const dataName = names.find((n) => n.startsWith(`API_${code}_`));
  const ctyName = names.find((n) => n.startsWith('Metadata_Country_'));
  if (!dataName || !ctyName) throw new Error(`${zip}: expected API_${code}_… and Metadata_Country_… inside`);
  const all = parseCSVRows(unzipText(zip, dataName));
  const lastUpdated = all.find((r) => r[0] === 'Last Updated Date')?.[1];
  const headAt = all.findIndex((r) => r[0] === 'Country Name');
  if (headAt < 0 || !lastUpdated) throw new Error(`${zip}: unexpected layout`);
  const head = all[headAt];
  const yearCols = head.map((h, i) => (/^\d{4}$/.test(h) ? [Number(h), i] : null)).filter(Boolean);
  const rows = all.slice(headAt + 1).filter((r) => r.length >= 4 && r[1]).map((r) => {
    if (r[3] !== code) throw new Error(`${zip}: row ${r[1]} has indicator ${r[3]}`);
    const values = {};
    for (const [y, i] of yearCols) if (r[i] !== '' && r[i] != null) values[y] = Number(r[i]);
    return { code: r[1], name: r[0], values };
  });
  const countryMeta = toObjects(parseCSVRows(unzipText(zip, ctyName)));
  return { lastUpdated, years: yearCols.map(([y]) => y), rows, countryMeta };
}

// ---------- main ----------
function main() {
  const codes = readFileSync(LIST, 'utf8').split('\n').map((l) => l.trim()).filter((l) => l && !l.startsWith('#'));
  const source = readFileSync(join(RAW, 'SOURCE.md'), 'utf8');
  const downloaded = (source.match(/Downloaded \(UTC\): (\S+)/) || [])[1];
  const indicators = {};
  const series = new Map(); // ISO3 → { name, values: { key: {year: v} } }
  let economies = null; // ISO3 → { region, incomeGroup, name, notes }

  for (const code of codes) {
    const L = LABELS[code];
    if (!L) throw new Error(`No site label for ${code} — add it to LABELS in scripts/build-wdi.mjs`);
    const zip = join(RAW, `${code}.zip`);
    if (!existsSync(zip)) throw new Error(`Missing ${zip} — run the "Fetch World Bank data (dev-data)" workflow`);
    const md = JSON.parse(readFileSync(join(RAW, `${code}.metadata.json`), 'utf8'));
    const mt = Object.fromEntries(md.source[0].concept[0].variable[0].metatype.map((m) => [m.id, m.value]));
    if (mt.License_Type !== 'CC BY-4.0') throw new Error(`${code}: licence is "${mt.License_Type}", not CC BY-4.0`);
    const buf = readFileSync(zip);
    const shaListed = (source.match(new RegExp(`\\| ${code.replace(/\./g, '\\.')} \\|.*\\| ([0-9a-f]{64}) \\|`)) || [])[1];
    if (shaListed !== sha(buf)) throw new Error(`${code}: zip SHA-256 does not match SOURCE.md`);
    const { lastUpdated, rows, countryMeta } = readWdiZip(zip, code);

    if (!economies) {
      economies = new Map();
      for (const c of countryMeta) {
        if (!c.Region) continue; // aggregates have no region
        economies.set(c['Country Code'], { region: c.Region, incomeGroup: c.IncomeGroup || null, name: c.TableName, notes: c.SpecialNotes || null });
      }
    }
    for (const r of rows) {
      let s = series.get(r.code);
      if (!s) series.set(r.code, (s = { name: r.name, values: {} }));
      s.values[L.key] = r.values;
    }
    indicators[L.key] = {
      code, label: L.label, unit: L.unit, wbName: mt.IndicatorName, source: mt.Source,
      licence: 'CC BY 4.0', licenceUrl: 'https://creativecommons.org/licenses/by/4.0/',
      aggregation: mt.Aggregationmethod ?? null, wdiLastUpdated: lastUpdated, file: `${code}.zip`, sha256: sha(buf),
      url: `https://data.worldbank.org/indicator/${code}`,
    };
  }
  if (!economies || economies.size < 200) throw new Error(`Only ${economies?.size} World Bank economies read`);

  const meta = {
    source: 'World Bank, World Development Indicators',
    sourceUrl: 'https://datacatalog.worldbank.org/search/dataset/0037712',
    licence: 'CC BY 4.0', licenceUrl: 'https://creativecommons.org/licenses/by/4.0/',
    terms: 'https://www.worldbank.org/ext/en/legal/terms-conditions/datasets',
    downloaded,
  };

  const keys = Object.keys(indicators);
  const pack = (values) => Object.fromEntries(keys.map((k) => {
    const v = values[k] || {};
    return [k, Object.entries(v).map(([y, x]) => [Number(y), x]).sort((a, b) => a[0] - b[0])];
  }));
  const latest = (pairs) => (pairs.length ? { year: pairs.at(-1)[0], value: pairs.at(-1)[1] } : null);

  rmSync(OUT, { recursive: true, force: true });
  mkdirSync(join(OUT, 'countries'), { recursive: true });
  const write = (p, o) => writeFileSync(join(OUT, p), JSON.stringify(o) + '\n');

  write('meta.json', { ...meta, indicators });
  const index = [];
  const aggregates = [];
  for (const [iso3, s] of series) {
    const data = pack(s.values);
    const e = economies.get(iso3);
    if (e) {
      write(`countries/${iso3}.json`, { iso3, wbName: e.name, region: e.region, incomeGroup: e.incomeGroup, notes: e.notes, series: data });
      index.push({ iso3, wbName: e.name, region: e.region, incomeGroup: e.incomeGroup, latest: Object.fromEntries(keys.map((k) => [k, latest(data[k])])) });
    } else aggregates.push({ code: iso3, name: s.name, series: data });
  }
  index.sort((a, b) => a.iso3.localeCompare(b.iso3));
  write('index.json', { meta, economies: index });
  write('aggregates.json', { meta, aggregates });

  // Match with the UN country list (pages use UN ISO3 codes)
  const un = JSON.parse(readFileSync('src/data/wpp/index.json', 'utf8')).countries.map((c) => c.iso3).filter(Boolean);
  const noWb = un.filter((c) => !economies.has(c));
  const noUn = [...economies.keys()].filter((c) => !un.includes(c));
  console.log(`✓ World Bank WDI: ${economies.size} economies + ${aggregates.length} aggregates, ${codes.length} indicators (WDI updated ${[...new Set(Object.values(indicators).map((i) => i.wdiLastUpdated))].join(', ')}).`);
  if (noUn.length) console.log(`  World Bank economies not in the UN list: ${noUn.join(', ')}`);
  if (noWb.length) console.log(`  UN countries/areas without World Bank data: ${noWb.length} (${noWb.join(', ')})`);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
