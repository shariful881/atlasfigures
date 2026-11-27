// shots (task 149): screenshots for showing the owner a batch — every page at 1280px and 390px, plus one
// contact sheet per width (all pages side by side) and full-length samples of the first pages.
// Starts `astro preview` on the last build if nothing is listening on the port.
//
//   node scripts/tools/shots.mjs /economy/denmark/ /economy/finland/ … [--out shots/142] [--full 2] [--port 4321]
//
// Needs Playwright and Chrome (in this workspace: /opt/npm-tools/node_modules/playwright, /usr/bin/google-chrome;
// override with PLAYWRIGHT and CHROME env vars).
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args.splice(i, 2)[1] : d; };
const out = resolve(opt('--out', 'shots'));
const full = Number(opt('--full', '2'));
const port = Number(opt('--port', '4321'));
const paths = args;
if (!paths.length) { console.error('usage: shots.mjs /path/ [/path/ …] [--out dir] [--full N]'); process.exit(2); }
const { chromium } = await import(process.env.PLAYWRIGHT || '/opt/npm-tools/node_modules/playwright/index.mjs');

const base = (() => { try { const m = readFileSync('astro.config.mjs', 'utf8').match(/base:\s*[^'"]*['"]([^'"]+)['"]/); return m ? m[1].replace(/\/$/, '') : ''; } catch { return ''; } })() || process.env.SITE_BASE?.replace(/\/$/, '') || '/atlasfigures';
const url = (p) => `http://localhost:${port}${base}${p}`;
let server = null;
async function up() { try { const r = await fetch(url('/')); return r.ok || r.status === 404; } catch { return false; } }
if (!(await up())) {
  server = spawn('npx', ['astro', 'preview', '--port', String(port)], { stdio: 'ignore' });
  for (let i = 0; i < 60 && !(await up()); i++) await new Promise((r) => setTimeout(r, 500));
}
mkdirSync(out, { recursive: true });
const b = await chromium.launch({ executablePath: process.env.CHROME || '/usr/bin/google-chrome' });
const made = { d: [], m: [] };
for (const [w, h, tag] of [[1280, 900, 'd'], [390, 844, 'm']]) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: tag === 'm' ? 2 : 1 });
  const p = await ctx.newPage();
  for (const [i, path] of paths.entries()) {
    const name = path.replace(/^\/|\/$/g, '').replace(/\//g, '_') || 'home';
    const res = await p.goto(url(path), { waitUntil: 'networkidle' });
    if (!res || res.status() >= 400) { console.error(`✗ ${path}: HTTP ${res?.status()}`); continue; }
    const first = join(out, `${name}-${tag}.png`);
    await p.screenshot({ path: first });
    made[tag].push({ name, path, file: first });
    if (i < full) await p.screenshot({ path: join(out, `${name}-${tag}-full.png`), fullPage: true });
  }
  await ctx.close();
}
// contact sheets: first screen of every page in a grid
for (const tag of ['d', 'm']) {
  if (!made[tag].length) continue;
  const cols = tag === 'd' ? 4 : 6, cw = tag === 'd' ? 320 : 195;
  const img = (f) => `data:image/png;base64,${readFileSync(f.file).toString('base64')}`;
  const html = `<!doctype html><meta charset="utf-8"><style>body{margin:0;padding:12px;font:12px system-ui;background:#eef1f4}
  .g{display:grid;grid-template-columns:repeat(${cols},${cw}px);gap:10px}figure{margin:0;background:#fff;border:1px solid #ccd;border-radius:6px;overflow:hidden}
  img{width:100%;display:block}figcaption{padding:4px 6px;color:#334}</style><div class="g">${made[tag].map((f) => `<figure><img src="${img(f)}"><figcaption>${f.path}</figcaption></figure>`).join('')}</div>`;
  const ctx = await b.newContext({ viewport: { width: cols * (cw + 10) + 24, height: 600 } });
  const p = await ctx.newPage(); await p.setContent(html, { waitUntil: 'load' });
  await p.screenshot({ path: join(out, `contact-sheet-${tag === 'd' ? '1280' : '390'}.png`), fullPage: true });
  await ctx.close();
}
await b.close();
server?.kill();
writeFileSync(join(out, 'index.txt'), paths.join('\n') + '\n');
console.log(`✓ ${made.d.length} desktop + ${made.m.length} mobile screenshots, contact sheets and ${Math.min(full, paths.length)} full samples in ${out}`);
