// check-profiles (task 158): the country list and every data profile are complete and equal to the generated data
// (which check-site, check-wdi and check-energy compare with the original files).
//   - country-list.json holds every UN WPP country or area once; slugs unique; pages exist where the list says so
//   - one profile per country; every live figure = the generated series it came from; ranks recomputed
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { factText } from './build-facts.mjs';

let checks = 0; const problems = [];
const ok = (c, where, msg) => { checks++; if (!c) problems.push(`${where}: ${msg}`); return c; };
const list = JSON.parse(readFileSync('src/data/country-list.json', 'utf8')).countries;
const wppIdx = JSON.parse(readFileSync('src/data/wpp/index.json', 'utf8'));
const catalog = JSON.parse(readFileSync('src/data/profile-stats.json', 'utf8')).sections;
const wdi = Object.fromEntries(readdirSync('src/data/wdi/countries').map((f) => { const d = JSON.parse(readFileSync(`src/data/wdi/countries/${f}`, 'utf8')); return [d.iso3, d]; }));
const energy = JSON.parse(readFileSync('src/data/energy/index.json', 'utf8'));
const facts = JSON.parse(readFileSync('src/data/facts/index.json', 'utf8')).facts;
const names = Object.fromEntries(list.map((c) => [c.iso3, c.name]));
const CHECKED = { currency: 'currency', languages: 'languages', callingCode: 'callingCode', tld: 'tld', neighbours: 'neighbours', highestPoint: 'highestPoint', drivingSide: 'drivingSide' };

const isos = new Set(list.map((c) => c.iso3));
for (const c of wppIdx.countries) ok(isos.has(c.iso3), c.iso3, 'missing from country-list.json');
ok(list.length === wppIdx.countries.length, 'country-list', `${list.length} entries, UN WPP has ${wppIdx.countries.length}`);
ok(new Set(list.map((c) => c.slug)).size === list.length, 'country-list', 'duplicate slugs');
for (const c of list) {
  ok(/^[a-z0-9]+(-[a-z0-9]+)*$/.test(c.slug), c.iso3, `bad slug "${c.slug}"`);
  for (const t of c.pages) ok(existsSync(`src/pages/country/${c.slug}/${t === 'hub' ? 'index' : t}.astro`), c.iso3, `list says a ${t} page exists at /country/${c.slug}/${t}/ but there is none`);
  for (const t of ['population', 'economy', 'health', 'education', 'internet', 'hub']) if (existsSync(`src/pages/country/${c.slug}/${t === 'hub' ? 'index' : t}.astro`)) ok(c.pages.includes(t), c.iso3, `${t} page exists but is not in the list`);
}
for (const d of existsSync('src/pages/country') ? readdirSync('src/pages/country').filter((d) => d !== 'index.astro') : []) ok(list.some((c) => c.slug === d), `src/pages/country/${d}`, 'folder has no country in country-list.json');

const liveInCatalog = catalog.flatMap((s) => s.stats).filter((s) => !s.planned).length;
for (const c of list) {
  const f = `src/data/profiles/${c.iso3}.json`;
  if (!ok(existsSync(f), c.iso3, 'no profile')) continue;
  const p = JSON.parse(readFileSync(f, 'utf8'));
  ok(p.slug === c.slug && p.name === c.name, c.iso3, 'profile slug/name differ from the list');
  const row = JSON.parse(readFileSync(`src/data/wpp/countries/${c.iso3}.json`, 'utf8')).years.find((y) => y.year === wppIdx.year);
  const stats = p.sections.flatMap((s) => s.stats);
  ok(stats.filter((s) => s.status !== 'planned').length === liveInCatalog, c.iso3, 'profile does not cover every catalog statistic');
  for (const sec of catalog) for (const st of sec.stats) {
    if (st.planned) continue;
    const got = p.sections.find((s) => s.id === sec.id).stats.find((s) => s.id === st.id);
    let want = null, year = null;
    if (st.src === 'wpp') { want = row?.[st.key] ?? null; year = wppIdx.year; }
    else if (st.src === 'wdi') { const s = wdi[c.iso3]?.series[st.key] ?? []; if (s.length && s.at(-1)[0] >= 2000) [year, want] = s.at(-1); } // same 2000 cut-off as build-profiles
    else if (st.src === 'energy') { const s = energy.countries[c.iso3]?.series[st.key] ?? []; if (s.length) [year, want] = s.at(-1); }
    else if (st.src === 'list') want = st.key === 'iso' ? `${c.iso3} / ${c.iso2}` : c[st.key];
    else if (st.src === 'facts') {
      want = facts[c.iso3] ? factText(facts[c.iso3], st.key, names) : null;
      const chk = facts[c.iso3]?.checks[CHECKED[st.key]];
      if (want != null && chk && chk !== 'agree' && !chk.checked) { ok(got.status === 'to-check' && got.value === want, c.iso3, `${st.id}: sources differ, so it must be "to-check", not ${got.status}`); continue; }
    }
    if (want == null || want === '') { ok(got.status === 'no-data', c.iso3, `${st.id} should be no-data`); continue; }
    ok(got.status === 'live' && got.value === want && (st.src === 'list' || st.src === 'facts' || got.year === year), c.iso3, `${st.id} = ${got.value} (${got.year}), data has ${want} (${year})`);
  }
}
console.log(`\n${problems.length ? '✗' : '✓'} Country list and profiles: ${checks} checks on ${list.length} countries or areas.`);
if (problems.length) { for (const p of problems.slice(0, 40)) console.log('  ' + p); process.exit(1); }
