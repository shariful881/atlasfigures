// build-profiles (task 158): one data profile per country or area — every statistic we hold for it, grouped in the
// sections of src/data/profile-stats.json, with year, unit, world rank and source; missing figures and planned
// statistics are listed too, so each profile shows what is still to come.
// Input: the generated data (src/data/wpp, src/data/wdi, src/data/energy) and src/data/country-list.json.
// Output (generated, git-ignored): src/data/profiles/<ISO3>.json and src/data/profiles/index.json.
// Runs in `npm run data` and before every build. Pages read profiles; nothing here is typed by hand.
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'node:fs';
import { factText } from './build-facts.mjs';

const OUT = 'src/data/profiles';
const list = JSON.parse(readFileSync('src/data/country-list.json', 'utf8')).countries;
const catalog = JSON.parse(readFileSync('src/data/profile-stats.json', 'utf8')).sections;
const wppIdx = JSON.parse(readFileSync('src/data/wpp/index.json', 'utf8'));
const YEAR = wppIdx.year; // the site's current year (UN projection for years after the last estimate)
const OLDEST = 2000; // World Bank figures from before this year are treated as missing (status no-data)
const wpp = Object.fromEntries(list.map((c) => [c.iso3, JSON.parse(readFileSync(`src/data/wpp/countries/${c.iso3}.json`, 'utf8'))]));
const wdiMeta = JSON.parse(readFileSync('src/data/wdi/meta.json', 'utf8'));
const wdi = Object.fromEntries(readdirSync('src/data/wdi/countries').map((f) => { const d = JSON.parse(readFileSync(`src/data/wdi/countries/${f}`, 'utf8')); return [d.iso3, d]; }));
const energy = JSON.parse(readFileSync('src/data/energy/index.json', 'utf8'));
const facts = JSON.parse(readFileSync('src/data/facts/index.json', 'utf8')); // task 156
const names = Object.fromEntries(list.map((c) => [c.iso3, c.name]));

const SRC = {
  wpp: 'UN World Population Prospects 2024',
  wup: 'UN World Urbanization Prospects 2025',
  wdi: 'World Bank, World Development Indicators',
  energy: { co2: 'Global Carbon Project', co2pc: 'Global Carbon Project' },
  list: 'UN WPP / World Bank classification',
  facts: { currency: 'Unicode CLDR; checked against GeoNames', languages: 'Unicode CLDR (national official status); checked against Wikidata', callingCode: 'GeoNames; checked against Wikidata', tld: 'GeoNames; checked against Wikidata', timeZones: 'IANA time zone database', neighbours: 'GeoNames (land borders); checked against Wikidata', landlocked: 'Wikidata', highestPoint: 'Wikidata', drivingSide: 'Wikidata', plugs: 'Wikidata (IEC plug types)', emergency: 'Wikidata' },
};
// which fact a second source checks (a differing check → "to-check", not live)
const CHECKED = { currency: 'currency', languages: 'languages', callingCode: 'callingCode', tld: 'tld', neighbours: 'neighbours', highestPoint: 'highestPoint', drivingSide: 'drivingSide' };
const fmtv = {
  int: (v) => Math.round(v).toLocaleString('en-US'), pct: (v) => `${v.toFixed(1).replace(/^-0\.0$/, '0.0')}%`, dec1: (v) => v.toFixed(1), dec2: (v) => v.toFixed(2),
  usd: (v) => (Math.abs(v) >= 1e12 ? `$${(v / 1e12).toFixed(2)} trillion` : Math.abs(v) >= 1e9 ? `$${(v / 1e9).toFixed(1)} billion` : Math.abs(v) >= 1e6 ? `$${(v / 1e6).toFixed(1)} million` : `$${Math.round(v).toLocaleString('en-US')}`),
  usdWhole: (v) => `$${Math.round(v).toLocaleString('en-US')}`, intd: (v) => `Int$${Math.round(v).toLocaleString('en-US')}`,
};
const rankOf = (values, iso3, lowFirst) => {
  const order = Object.entries(values).sort((a, b) => (lowFirst ? a[1] - b[1] : b[1] - a[1]) || a[0].localeCompare(b[0]));
  const i = order.findIndex(([k]) => k === iso3);
  return i < 0 ? null : { rank: i + 1, of: order.length };
};
// WDI: each economy at its latest year from (since ?? latest-5) on, like rankLatest in src/lib/econ.ts
const wdiLatest = (key, since) => Object.fromEntries(Object.values(wdi).map((d) => { const s = (d.series[key] ?? []).filter(([y]) => y >= since); return s.length ? [d.iso3, s.at(-1)[1]] : null; }).filter(Boolean));
const yearRow = (iso3) => wpp[iso3].years.find((y) => y.year === YEAR);
const wppAll = (key) => Object.fromEntries(list.map((c) => [c.iso3, yearRow(c.iso3)?.[key]]).filter(([, v]) => v != null));
const enLatest = (key, year) => Object.fromEntries(Object.values(energy.countries).map((c) => [c.iso3, c.series[key]?.find(([y]) => y === year)?.[1]]).filter(([, v]) => v != null));

mkdirSync(OUT, { recursive: true });
const index = [];
for (const c of list) {
  const sections = catalog.map((sec) => ({
    id: sec.id, label: sec.label,
    stats: sec.stats.map((st) => {
      if (st.planned) return { label: st.label, status: 'planned', phase: st.planned, source: st.source };
      let value = null, year = null, rank = null, source = SRC[st.src], projection = false, text = null;
      if (st.src === 'list') {
        value = st.key === 'iso' ? `${c.iso3} / ${c.iso2}` : c[st.key];
        text = value;
      } else if (st.src === 'wpp') {
        const row = yearRow(c.iso3);
        value = row?.[st.key] ?? null; year = YEAR; projection = !!row?.projection;
        if (st.key === 'urbanPct') source = SRC.wup;
        if (value != null && st.rank) rank = rankOf(wppAll(st.key), c.iso3, st.rank === 'low');
      } else if (st.src === 'wdi') {
        const s = wdi[c.iso3]?.series[st.key] ?? [];
        // a latest figure older than OLDEST is not shown as the country's figure (e.g. Nigeria's exports stop in 1960)
        if (s.length && s.at(-1)[0] >= OLDEST) {
          [year, value] = s.at(-1);
          if (st.rank) rank = rankOf(wdiLatest(st.key, st.since ?? year - 5), c.iso3, st.rank === 'low');
          source = `${SRC.wdi} (${wdiMeta.indicators[st.key]?.code})`;
        }
      } else if (st.src === 'facts') {
        const f = facts.facts[c.iso3];
        source = SRC.facts[st.key];
        value = f ? factText(f, st.key, names) : null;
        text = value;
        const chk = f?.checks[CHECKED[st.key]];
        if (value != null && chk && chk !== 'agree' && !chk.checked) return { id: st.id, label: st.label, status: 'to-check', value, text, source, differ: chk.differ };
      } else if (st.src === 'energy') {
        const s = energy.countries[c.iso3]?.series[st.key] ?? [];
        if (s.length) { [year, value] = s.at(-1); if (st.rank) rank = rankOf(enLatest(st.key, year), c.iso3, st.rank === 'low'); }
        source = SRC.energy[st.key] ?? 'Ember';
      }
      if (value == null || value === '') return { id: st.id, label: st.label, status: 'no-data', source };
      if (text == null) text = fmtv[st.fmt](value);
      return { id: st.id, label: st.label, status: 'live', value, text, unit: st.unit ?? null, year, projection: projection || undefined, rank: rank?.rank, of: rank?.of, rankBy: rank ? st.rank : undefined, source };
    }),
  }));
  const all = sections.flatMap((s) => s.stats);
  const coverage = { live: all.filter((s) => s.status === 'live').length, toCheck: all.filter((s) => s.status === 'to-check').length, noData: all.filter((s) => s.status === 'no-data').length, planned: all.filter((s) => s.status === 'planned').length };
  const profile = { iso3: c.iso3, iso2: c.iso2, slug: c.slug, name: c.name, unName: c.unName, unRegion: c.unRegion, unSubregion: c.unSubregion, pages: c.pages, year: YEAR, coverage, sections };
  writeFileSync(`${OUT}/${c.iso3}.json`, JSON.stringify(profile));
  index.push({ iso3: c.iso3, slug: c.slug, name: c.name, unSubregion: c.unSubregion, pages: c.pages, ...coverage });
}
writeFileSync(`${OUT}/index.json`, JSON.stringify({ year: YEAR, count: index.length, liveStatsInCatalog: catalog.flatMap((s) => s.stats).filter((s) => !s.planned).length, countries: index }));
const live = index.map((x) => x.live);
console.log(`✓ profiles: ${index.length} countries or areas, ${Math.min(...live)}–${Math.max(...live)} live statistics each (median ${live.sort((a, b) => a - b)[Math.floor(live.length / 2)]})`);
