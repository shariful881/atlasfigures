// check-country-pages (task 160): country hubs (/country/<slug>/) and topic pages (/country/<slug>/<topic>/)
// written from task 160 on, one editorial JSON each in src/data/country-pages/. After `astro build`:
//   - every statistic row on the page = the country profile (text, year, rank), and the rows are exactly the
//     profile's live statistics (single-source facts only with a hand check recorded in the JSON, with its URL)
//   - hub CSV = the same rows; health CSV = the World Bank values exactly; health table cells = rounded values
//   - every number in the JSON-LD (headline, description, Dataset, FAQ) is shown on the page; FAQ schema = page
//   - Published/Updated shown; Updated = Article dateModified = Dataset dateModified = sitemap lastmod
// Generic rules (closed FAQ/Sources, Report an error, links, number style) are check-site's.
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'node-html-parser';

const DIST = process.argv[2] || 'dist';
const BASE = '/atlasfigures';
const problems = [];
let checks = 0;
const ok = (c, where, what) => { checks++; if (!c) problems.push(`${where}: ${what}`); return c; };
const textOf = (el) => el.text.replace(/\s+/g, ' ').trim();
const nodes = (root) => root.querySelectorAll('script[type="application/ld+json"]').flatMap((s) => { const d = JSON.parse(s.text); return d['@graph'] ?? [d]; });
const sitemap = existsSync(join(DIST, 'sitemap.xml')) ? readFileSync(join(DIST, 'sitemap.xml'), 'utf8') : '';
const lastmod = (u) => (sitemap.match(new RegExp(`<loc>[^<]*${BASE}${u.replace(/\//g, '\\/')}</loc><lastmod>([^<]+)</lastmod>`)) || [])[1];
const SINGLE = new Set(['landlocked', 'highest', 'driving', 'plugs', 'emergency']);
const ordinal = (n) => { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`; };
const csvRows = (txt) => txt.split('\n').filter((l) => l && !l.startsWith('#')).map((l) => { const out = []; let f = '', q = false; for (const ch of l) { if (q) { if (ch === '"') q = false; else f += ch; } else if (ch === '"') q = true; else if (ch === ',') { out.push(f); f = ''; } else f += ch; } out.push(f); return out; });

const dir = 'src/data/country-pages';
const pages = existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.json')).map((f) => JSON.parse(readFileSync(join(dir, f), 'utf8'))) : [];
const HEALTH = ['under5Mortality', 'infantMortality', 'neonatalMortality', 'maternalMortality', 'measlesVaccPct', 'healthSpendPctGdp', 'outOfPocketPct'];
const HEALTH_DIGITS = [1, 1, 1, 0, 0, 1, 1];

for (const c of pages) {
  const prof = JSON.parse(readFileSync(`src/data/profiles/${c.iso3}.json`, 'utf8'));
  const wdi = JSON.parse(readFileSync(`src/data/wdi/countries/${c.iso3}.json`, 'utf8')).series;
  for (const f of c.checkedFacts ?? []) ok((c.factChecks ?? []).some((x) => x.fact === f && /^https?:\/\//.test(x.url) && x.checkedOn), `${c.slug}`, `fact "${f}" is shown without a recorded hand check (factChecks with url and checkedOn)`);
  for (const [topic, meta] of Object.entries(c.pages)) {
    const url = topic === 'hub' ? `/country/${c.slug}/` : `/country/${c.slug}/${topic}/`;
    const where = `page ${url}`;
    const file = join(DIST, url, 'index.html');
    if (!ok(existsSync(file), where, 'page not built')) continue;
    const html = readFileSync(file, 'utf8');
    const root = parse(html);
    const text = textOf(parse(html.replace(/<script[\s\S]*?<\/script>|<style[\s\S]*?<\/style>/g, '')));

    // statistic rows = profile
    const shown = root.querySelectorAll('.stat-list tr[data-stat]');
    const want = [];
    for (const sec of prof.sections) for (const s of sec.stats) {
      if (s.status !== 'live') continue;
      if (sec.id === 'facts' && SINGLE.has(s.id) && !(c.checkedFacts ?? []).includes(s.id)) continue;
      want.push({ key: `${sec.id}.${s.id}`, s });
    }
    const wantHere = topic === 'hub' ? want : want.filter((w) => w.key.startsWith(`${topic}.`));
    ok(shown.length === wantHere.length, where, `${shown.length} statistic rows, profile has ${wantHere.length} live`);
    for (const tr of shown) {
      const key = tr.getAttribute('data-stat');
      const w = wantHere.find((x) => x.key === key);
      if (!ok(w, where, `row ${key} is not a live profile statistic`)) continue;
      const v = textOf(tr.querySelector('[data-value]'));
      ok(v === w.s.text, where, `${key}: page "${v}" ≠ profile "${w.s.text}"`);
      const y = textOf(tr.querySelector('.sl-y'));
      ok(w.s.year == null ? y === '' : y.startsWith(String(w.s.year)), where, `${key}: year "${y}" ≠ ${w.s.year}`);
      ok(!!w.s.projection === y.includes('UN projection'), where, `${key}: UN projection label`);
      const r = textOf(tr.querySelector('.sl-r'));
      ok(w.s.rank ? r === `${ordinal(w.s.rank)} ${w.s.rankBy === 'low' ? 'lowest' : 'highest'} of ${w.s.of}` : r === '', where, `${key}: rank "${r}"`);
    }

    // CSV
    if (topic === 'hub') {
      const csv = join(DIST, 'data', `${c.slug}-profile.csv`);
      if (ok(existsSync(csv), where, 'profile CSV not built')) {
        const rows = csvRows(readFileSync(csv, 'utf8'));
        ok(rows.length - 1 === want.length, where, `CSV has ${rows.length - 1} rows, page ${want.length}`);
        rows.slice(1).forEach((r, i) => { const s = want[i]?.s; ok(s && r[1] === s.label && r[2] === String(s.value) && r[3] === s.text && r[5] === String(s.year ?? '') && r[7] === String(s.rank ?? ''), where, `CSV row ${i + 1} (${r[1]}) ≠ profile`); });
      }
    }
    if (topic === 'health') {
      const rowsEl = root.querySelectorAll('table.topic tbody tr');
      ok(rowsEl.length === meta.tableYears.length, where, `table has ${rowsEl.length} rows, tableYears ${meta.tableYears.length}`);
      for (const tr of rowsEl) {
        const y = Number(tr.getAttribute('data-year'));
        const got = tr.querySelectorAll('td').map(textOf);
        const exp = HEALTH.map((k, i) => { const m = new Map(wdi[k]); return m.has(y) ? m.get(y).toLocaleString('en-US', { minimumFractionDigits: HEALTH_DIGITS[i], maximumFractionDigits: HEALTH_DIGITS[i] }) : '–'; });
        ok(JSON.stringify(got) === JSON.stringify(exp), where, `table ${y}: ${JSON.stringify(got)} ≠ data ${JSON.stringify(exp)}`);
      }
      const csv = join(DIST, 'data', `${c.slug}-health.csv`);
      if (ok(existsSync(csv), where, 'health CSV not built')) {
        const rows = csvRows(readFileSync(csv, 'utf8'));
        const head = rows[0];
        const meta2 = JSON.parse(readFileSync('src/data/wdi/meta.json', 'utf8')).indicators;
        const codeOf = Object.fromEntries(readFileSync(csv, 'utf8').split('\n').find((l) => l.startsWith('# Codes:')).slice(9).split('; ').map((x) => x.split('=')));
        for (const r of rows.slice(1)) {
          const y = Number(r[0]);
          head.slice(1).forEach((h, i) => {
            const key = Object.entries(meta2).find(([, m]) => m.code === codeOf[h])?.[0];
            const m = new Map(wdi[key]);
            ok(r[i + 1] === (m.has(y) ? String(m.get(y)) : ''), where, `CSV ${h} ${y}: ${r[i + 1]} ≠ World Bank ${m.get(y)}`);
          });
        }
      }
    }

    // schema and dates
    const n = nodes(root);
    const art = n.find((x) => x['@type'] === 'Article'), ds = n.find((x) => x['@type'] === 'Dataset'), fq = n.find((x) => x['@type'] === 'FAQPage');
    if (!ok(art && ds && fq, where, 'country page needs Article + Dataset + FAQPage')) continue;
    ok(art.about?.['@type'] === 'Country', where, 'Article about Country missing');
    for (const t of [art.headline, art.description, ds.name, ds.description, ...fq.mainEntity.flatMap((q) => [q.name, q.acceptedAnswer.text])]) {
      for (const num of t.match(/\d[\d,]*(\.\d+)?/g) ?? []) ok(text.includes(num), where, `JSON-LD number ${num} is not shown on the page`);
    }
    ok(JSON.stringify(root.querySelectorAll('.faq details summary').map(textOf)) === JSON.stringify(fq.mainEntity.map((q) => q.name)), where, 'FAQ in JSON-LD differs from the page');
    ok(art.datePublished?.startsWith(meta.published), where, `datePublished ≠ Published ${meta.published}`);
    ok(art.dateModified?.startsWith(meta.updated) && ds.dateModified?.startsWith(meta.updated), where, `dateModified ≠ Updated ${meta.updated}`);
    ok(root.querySelectorAll('time').some((t) => t.getAttribute('datetime') === meta.updated), where, 'Updated date not shown');
    ok(lastmod(url) === meta.updated, where, `sitemap lastmod ${lastmod(url)} ≠ Updated ${meta.updated}`);
    ok((meta.changelog ?? []).length > 0, where, 'changelog empty');
    if (meta.verification) ok(root.querySelectorAll('.vchip, .badge').length > 0 || html.includes('Verified'), where, 'verification recorded but no Verified badge');
  }
}

console.log(`\n${problems.length ? '✗' : '✓'} Country hubs and topic pages: ${checks} checks on ${pages.reduce((n, c) => n + Object.keys(c.pages).length, 0)} page(s).`);
if (problems.length) { for (const p of problems.slice(0, 40)) console.log('  ' + p); process.exit(1); }
