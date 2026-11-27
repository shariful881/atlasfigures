// check-sources (task 149): has any source published a new version, or become unreachable?
// Reads data/sources.json and the SOURCE.md records of what we hold. Needs internet (runs weekly in
// .github/workflows/watch-sources.yml; the workspace sandbox cannot reach these hosts).
//
//   node scripts/tools/check-sources.mjs [--report report.md] [--json result.json]
//
// Statuses: same · new (a newer version exists) · unreachable (every address failed) · error.
// It never changes data itself. The workflow decides: autoFetch sources are re-fetched into a new
// `data-update-YYYYMMDD` branch (from main) and opened as a pull request into main; everything else becomes a GitHub issue.
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const reg = JSON.parse(readFileSync('data/sources.json', 'utf8'));
const UA = { 'User-Agent': 'AtlasFigures source check (github.com/shariful881/atlasfigures)' };

const recorded = (raw, file) => {
  const md = existsSync(`${raw}/SOURCE.md`) ? readFileSync(`${raw}/SOURCE.md`, 'utf8') : '';
  const row = md.split('\n').find((l) => l.includes(`| ${file} |`) || l.includes(`${file} |`));
  return row?.match(/\b[0-9a-f]{64}\b/)?.[0] ?? null;
};
async function get(url, asBuffer = false) {
  const r = await fetch(url, { headers: UA, redirect: 'follow' });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return asBuffer ? Buffer.from(await r.arrayBuffer()) : r.json();
}

const results = [];
for (const s of reg.sources.filter((x) => x.status === 'active')) {
  const res = { id: s.id, name: s.name, fetch: s.fetch, autoFetch: s.autoFetch, status: 'same', held: '', found: '', note: s.check.note ?? '' };
  try {
    if (s.check.type === 'wdi') {
      const md = readFileSync(`${s.raw}/SOURCE.md`, 'utf8');
      res.held = [...md.matchAll(/\| (\d{4}-\d{2}-\d{2}) \| https:\/\/api\.worldbank/g)].map((m) => m[1]).sort().at(-1);
      const j = await get(s.check.api);
      res.found = j?.[1]?.[0]?.lastupdated;
      if (!res.found) throw new Error('no lastupdated in the World Bank API answer');
      if (res.found > res.held) res.status = 'new';
    } else if (s.check.type === 'sha') {
      res.held = recorded(s.raw, s.check.file)?.slice(0, 12) ?? '(not recorded)';
      const urls = [...s.check.urls, ...(s.backups ?? [])];
      let buf = null, errs = [];
      for (const u of urls) { try { buf = await get(u, true); res.from = u; break; } catch (e) { errs.push(e.message); } }
      if (!buf) { res.status = 'unreachable'; res.note = errs.join('; '); }
      else {
        res.found = createHash('sha256').update(buf).digest('hex').slice(0, 12);
        if (res.found !== res.held) res.status = 'new';
        if (res.from !== s.check.urls[0]) res.note += ` (main address failed — got it from backup ${res.from})`;
      }
    } else if (s.check.type === 'zenodo-latest') {
      res.held = s.check.record;
      const j = await get(`https://zenodo.org/api/records/${s.check.record}/versions/latest`);
      res.found = String(j.id);
      if (res.found !== res.held) { res.status = 'new'; res.note = `new version ${j.metadata?.version ?? ''} (${j.metadata?.publication_date ?? ''}), licence ${j.metadata?.license?.id ?? '?'} — update GCB_RECORD/GCB_VERSION in fetch-energy.yml by hand`; }
    }
  } catch (e) { res.status = res.status === 'same' ? 'error' : res.status; res.note = e.message; }
  results.push(res);
  console.log(`${res.status.padEnd(11)} ${s.id.padEnd(8)} held ${res.held || '-'} · found ${res.found || '-'} ${res.note}`);
}

const planned = reg.sources.filter((x) => x.status === 'planned');
const attention = results.filter((r) => r.status !== 'same');
const dispatch = [...new Set(results.filter((r) => r.status === 'new' && r.autoFetch).map((r) => r.fetch))];
const report = [
  `# Data sources check — ${new Date().toISOString().slice(0, 10)}`, '',
  '| Source | Status | Held | Found | Note |', '|---|---|---|---|---|',
  ...results.map((r) => `| ${r.name} | ${r.status === 'same' ? '✅ same' : r.status === 'new' ? '🆕 new version' : '⚠️ ' + r.status} | ${r.held || '–'} | ${r.found || '–'} | ${r.note.replace(/\|/g, '/')} |`), '',
  dispatch.length ? `Re-fetching automatically into a new \`data-update-YYYYMMDD\` branch: ${dispatch.join(', ')}. A pull request into main follows, with the check results. It goes live after the checks and a re-verification of the changed figures.` : '',
  attention.some((r) => r.status === 'new' && !r.autoFetch) ? 'Sources marked new without automatic fetching need a hand update (see notes).' : '',
  attention.some((r) => ['unreachable', 'error'].includes(r.status)) ? 'Unreachable sources keep their current data. If an address keeps failing, find the same file elsewhere, check it by hand, and add it under "backups" in data/sources.json.' : '',
  '', `Planned sources (not yet fetched): ${planned.map((p) => `${p.name} (task ${p.task})`).join('; ')}.`,
].filter((l) => l !== null).join('\n');
if (opt('--report')) writeFileSync(opt('--report'), report + '\n');
if (opt('--json')) writeFileSync(opt('--json'), JSON.stringify({ attention: attention.length, dispatch, results }, null, 2));
if (!opt('--report')) console.log('\n' + report);
