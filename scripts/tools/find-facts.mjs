// find-facts (task 149): story-ready facts for one or more countries, each with the matching
// assertClaim line for the page (src/lib/claims.ts) and the matching line for the independent verify
// script (scripts/verify/_wdi.py). Reads the generated World Bank data (src/data/wdi/) — run `npm run data` first.
//
//   node scripts/tools/find-facts.mjs BGD IND            # all indicators
//   node scripts/tools/find-facts.mjs BGD --only gdp,remittances --out tmp/facts-bgd.md
//
// It only FINDS candidates. Every fact still has to be read, chosen and written by hand, and checked
// against the original files by the verify script before publishing (CLAUDE.md, data guide).
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : null; };
const out = opt('--out');
const only = opt('--only')?.split(',');
const isos = args.map((a) => a.toUpperCase());
if (!isos.length) { console.error('usage: find-facts.mjs ISO3 [ISO3...] [--only key,key] [--out file.md]'); process.exit(2); }

const DIR = 'src/data/wdi';
const meta = JSON.parse(readFileSync(`${DIR}/meta.json`, 'utf8'));
const all = Object.fromEntries(readdirSync(`${DIR}/countries`).map((f) => { const d = JSON.parse(readFileSync(`${DIR}/countries/${f}`, 'utf8')); return [d.iso3, d]; }));
const IND = Object.entries(meta.indicators).filter(([k]) => !only || only.includes(k));

// ---- helpers (same rules as src/lib/claims.ts) ----
const at = (s, y) => s.find(([x]) => x === y)?.[1];
const highestSince = (s, y) => { const v = at(s, y); const p = s.filter(([x, w]) => x < y && w >= v); return p.length ? p.at(-1)[0] : null; };
const lowestSince = (s, y) => { const v = at(s, y); const p = s.filter(([x, w]) => x < y && w <= v); return p.length ? p.at(-1)[0] : null; };
function streak(s) {
  if (s.length < 2) return { dir: 'flat', years: 0, from: 0 };
  const sg = (i) => Math.sign(s[i][1] - s[i - 1][1]); const d = sg(s.length - 1); let i = s.length - 1;
  while (i > 0 && s[i][0] - s[i - 1][0] === 1 && sg(i) === d && d !== 0) i--;
  return { dir: d > 0 ? 'up' : d < 0 ? 'down' : 'flat', years: s.length - 1 - i, from: s[i][0] };
}
const aboveSince = (s, t) => { if (!s.length || s.at(-1)[1] <= t) return null; let i = s.length - 1; while (i > 0 && s[i - 1][1] > t) i--; return s[i][0]; };
const belowSince = (s, t) => { if (!s.length || s.at(-1)[1] >= t) return null; let i = s.length - 1; while (i > 0 && s[i - 1][1] < t) i--; return s[i][0]; };
function rankLatest(key, since, keep = () => true) {
  return Object.values(all).map((d) => { const s = (d.series[key] ?? []).filter(([y]) => y >= since); return s.length && keep(d) ? { iso3: d.iso3, value: s.at(-1)[1], year: s.at(-1)[0] } : null; })
    .filter(Boolean).sort((a, b) => b.value - a.value || a.iso3.localeCompare(b.iso3)).map((x, i) => ({ ...x, rank: i + 1 }));
}

// ---- number style for the fact text ----
const kind = (m) => (m.unit.includes('US$') || m.unit.includes('international $') ? 'money' : m.unit.startsWith('%') || m.unit.includes('% of') || m.unit.includes('%') ? 'pct' : m.unit.includes('per 100 ') ? 'per100' : m.unit.includes('per 1,000') || m.unit.includes('per 100,000') ? 'rate' : 'count');
const money = (v) => (Math.abs(v) >= 1e12 ? `$${(v / 1e12).toFixed(2)} trillion` : Math.abs(v) >= 1e9 ? `$${(v / 1e9).toFixed(1)} billion` : Math.abs(v) >= 1e6 ? `$${(v / 1e6).toFixed(1)} million` : `$${Math.round(v).toLocaleString('en-US')}`);
const fmt = (m, v) => ({ money: money(v), pct: `${v.toFixed(1)}%`, per100: v.toFixed(1), rate: v.toFixed(1), count: v >= 1e6 ? `${(v / 1e6).toFixed(1)} million` : Math.round(v).toLocaleString('en-US') })[kind(m)];
const ord = (n) => `${n}${n % 100 >= 11 && n % 100 <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' })[n % 10] ?? 'th'}`;
const THRESH = { pct: [5, 10, 20, 25, 50, 75, 90], per100: [10, 50, 100], rate: [10, 25, 50, 100], money: [], count: [] };

const lines = [];
const W = (s = '') => lines.push(s);
W(`# find-facts — ${isos.join(', ')} (World Bank WDI, downloaded ${meta.downloaded})`);
W('');
W('Candidates only. Choose, write in your own words, keep each sentence\'s assertClaim, and add the Python line to the verify script.');
W('Python setup for the verify script:');
W('```python');
W(`import sys; sys.path.insert(0, 'scripts/verify'); from _wdi import *`);
W(`S = {c: wdi(c) for c in ${JSON.stringify(IND.map(([, m]) => m.code))}}`);
W('```');

for (const iso of isos) {
  const d = all[iso];
  if (!d) { W(`\n## ${iso}: no World Bank data`); continue; }
  W(`\n## ${d.wbName} (${iso}) — ${d.region}, ${d.incomeGroup ?? 'no income group'}`);
  W('TypeScript setup: `const s = econData(\'' + iso + '\').series;` and `import { highestSince, lowestSince, streak, aboveSince, belowSince, times } from \'../../lib/claims\'; (rankLatest, valueIn from econ)`');
  for (const [key, m] of IND) {
    const s = d.series[key] ?? [];
    if (s.length < 3) continue;
    const [L, v] = s.at(-1);
    const PY = `S['${m.code}']['${iso}']`;
    const facts = [];
    const add = (text, ts, py) => facts.push({ text, ts, py });
    const k = kind(m);

    // record high / low, or highest/lowest for a long time
    const hs = highestSince(s, L), ls = lowestSince(s, L);
    if (hs === null) add(`${L}: ${fmt(m, v)} — highest on record (series from ${s[0][0]})`, `highestSince(s.${key}, ${L}) === null`, `highest_since(${PY}, ${L}) is None`);
    else if (L - hs >= 8) add(`${L}: ${fmt(m, v)} — highest since ${hs}`, `highestSince(s.${key}, ${L}) === ${hs}`, `highest_since(${PY}, ${L}) == ${hs}`);
    if (ls === null) add(`${L}: ${fmt(m, v)} — lowest on record (series from ${s[0][0]})`, `lowestSince(s.${key}, ${L}) === null`, `lowest_since(${PY}, ${L}) is None`);
    else if (L - ls >= 8) add(`${L}: ${fmt(m, v)} — lowest since ${ls}`, `lowestSince(s.${key}, ${L}) === ${ls}`, `lowest_since(${PY}, ${L}) == ${ls}`);

    // runs of rises or falls
    const st = streak(s);
    if (st.years >= 4) add(`${st.dir === 'up' ? 'rose' : 'fell'} ${st.years} years in a row (${st.from}–${L})`, `(() => { const r = streak(s.${key}); return r.dir === '${st.dir}' && r.years === ${st.years} && r.from === ${st.from}; })()`, `streak(${PY}) == ('${st.dir}', ${st.years}, ${st.from})`);

    // thresholds crossed in the last ten years (and still on that side)
    for (const t of THRESH[k]) {
      const a = aboveSince(s, t);
      if (a != null && a >= L - 9 && a > s[0][0]) add(`above ${t}${k === 'pct' ? '%' : ''} since ${a} (every year after)`, `aboveSince(s.${key}, ${t}) === ${a}`, `above_since(${PY}, ${t}) == ${a}`);
      const b = belowSince(s, t);
      if (b != null && b >= L - 9 && b > s[0][0]) add(`below ${t}${k === 'pct' ? '%' : ''} since ${b} (every year after)`, `belowSince(s.${key}, ${t}) === ${b}`, `below_since(${PY}, ${t}) == ${b}`);
    }
    // growth: positive every year since …
    if (key.endsWith('GrowthPct')) {
      const p = aboveSince(s, 0);
      if (p != null && L - p >= 5) add(`positive every year since ${p}${p > s[0][0] ? ` (last fall: ${s.filter(([y, x]) => y < p && x <= 0).at(-1)?.[0]})` : ' (no fall on record)'}`, `aboveSince(s.${key}, 0) === ${p}`, `above_since(${PY}, 0) == ${p}`);
    }
    // change since 2000 / 1990
    for (const y0 of [1990, 2000]) {
      const a = at(s, y0);
      if (a && k !== 'pct' && (v / a >= 2 || v / a <= 0.5)) add(`${(v / a).toFixed(1)} times its ${y0} level (${fmt(m, a)} → ${fmt(m, v)})`, `times(s.${key}, ${y0}, ${L}) ${v / a >= 2 ? `> ${Math.floor(v / a)}` : `< ${(Math.ceil(v / a * 10) / 10).toFixed(1)}`}`, `times(${PY}, ${y0}, ${L}) ${v / a >= 2 ? `> ${Math.floor(v / a)}` : `< ${(Math.ceil(v / a * 10) / 10).toFixed(1)}`}`);
      if (a != null && k === 'pct' && Math.abs(v - a) >= 10) add(`${fmt(m, a)} in ${y0} → ${fmt(m, v)} in ${L} (${(v - a > 0 ? '+' : '')}${(v - a).toFixed(1)} points)`, `valueIn(s.${key}, ${y0}) === ${a} && valueIn(s.${key}, ${L}) === ${v}`, `${PY}[${y0}] == ${a} and ${PY}[${L}] == ${v}`);
    }
    // world and regional place (each country at its latest year from L-5 on)
    const since = L - 5;
    const w = rankLatest(key, since), me = w.find((r) => r.iso3 === iso);
    if (me) {
      const flag = me.rank <= 10 ? ' ★ top 10' : me.rank > w.length - 10 ? ' ★ bottom 10' : '';
      add(`world: ${ord(me.rank)} of ${w.length}${flag}`, `rankLatest('${key}', ${since}).find((r) => r.iso3 === '${iso}')!.rank === ${me.rank}`, `rank_latest(S['${m.code}'], '${iso}', ${since}) == (${me.rank}, ${w.length})`);
      const rg = rankLatest(key, since, (x) => x.region === d.region), rm = rg.find((r) => r.iso3 === iso);
      if (rm && rg.length >= 4 && (rm.rank <= 3 || rm.rank === rg.length)) add(`${d.region}: ${ord(rm.rank)} of ${rg.length}${rm.rank === rg.length ? ' (lowest)' : rm.rank === 1 ? ' (highest)' : ''} — ${rg.slice(0, 3).map((r) => `${r.iso3} ${fmt(m, r.value)}`).join(', ')}`, `rankLatest('${key}', ${since}).filter((r) => r.region === '${d.region}').findIndex((r) => r.iso3 === '${iso}') === ${rm.rank - 1}`, `rank_latest(S['${m.code}'], '${iso}', ${since}, region('${d.region}')) == (${rm.rank}, ${rg.length})`);
    }
    if (!facts.length) continue;
    W(`\n### ${m.label} — ${fmt(m, v)} (${L}) · \`${key}\` · ${m.code}`);
    for (const f of facts) {
      W(`- ${f.text}`);
      W(`  - TS: \`assertClaim(${f.ts}, '…');\``);
      W(`  - PY: \`claim(slug, '…', ${f.py})\``);
    }
  }
}

const text = lines.join('\n') + '\n';
if (out) { mkdirSync(dirname(out), { recursive: true }); writeFileSync(out, text); console.log(`wrote ${out} (${lines.length} lines)`); }
else process.stdout.write(text);
