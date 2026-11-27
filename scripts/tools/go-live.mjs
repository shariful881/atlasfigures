// go-live (task 149): the owner's go-live steps in one command — ONLY after the owner has explicitly said to
// make this piece of work live ("live koro"). One approval covers one piece of work (CLAUDE.md).
//
//   node scripts/tools/go-live.mjs --task 149 --approved "১৪৯ live কর" --title "Tools: find-facts, …" \
//        --body-file /tmp/pr.md [--verify scripts/verify/econ-batch20.py --verify …]
//
// Steps: refuse unless on dev / dev-data with a clean tree → merge the latest origin/main → npm run check and
// every --verify script → push → open (or reuse) the PR into main → wait for the `check` job → merge →
// wait for "Deploy to GitHub Pages" on main → fast-forward the branch to main and push.
// Uses git and `gh api` (authenticated as the repo owner in this workspace). Never force-pushes.
import { execSync, spawnSync } from 'node:child_process';
import { readFileSync } from 'node:fs';

const args = process.argv.slice(2);
const all = (k) => { const v = []; let i; while ((i = args.indexOf(k)) >= 0) v.push(args.splice(i, 2)[1]); return v; };
const one = (k) => all(k)[0];
const REPO = 'shariful881/atlasfigures';
const task = one('--task'), approved = one('--approved'), title = one('--title'), bodyFile = one('--body-file'), verify = all('--verify');
const die = (m) => { console.error(`✗ ${m}`); process.exit(1); };
if (!task || !approved || !title || !bodyFile) die('need --task, --approved "<owner\'s words>", --title and --body-file');
if (!/live/i.test(approved)) die(`--approved must be the owner's go-live words (e.g. "${task} live কর"), got "${approved}"`);

const sh = (c, o = {}) => execSync(c, { stdio: ['ignore', 'pipe', 'inherit'], encoding: 'utf8', ...o }).trim();
const run = (c) => { console.log(`$ ${c}`); const r = spawnSync(c, { shell: true, stdio: 'inherit' }); if (r.status !== 0) die(`failed: ${c}`); };
const api = (path, flags = '') => JSON.parse(sh(`gh api ${flags} repos/${REPO}/${path}`));
const sleep = (s) => new Promise((r) => setTimeout(r, s * 1000));

const branch = sh('git rev-parse --abbrev-ref HEAD');
if (!['dev', 'dev-data', 'dev-site'].includes(branch)) die(`on "${branch}" — go live only from dev, dev-data or dev-site`);
if (sh('git status --porcelain')) die('working tree not clean — commit first');

console.log(`\n== Task ${task}: going live from ${branch} (owner said: "${approved}")`);
run('git fetch origin');
if (sh(`git rev-list --count HEAD..origin/main`) !== '0') run('git merge --no-edit origin/main');
run('npm run check');
for (const v of verify) run(`python3 ${v}`);
run(`git push origin ${branch}`);

let pr = api(`pulls?head=${REPO.split('/')[0]}:${branch}&base=main&state=open`)[0];
if (!pr) {
  pr = JSON.parse(sh(`gh api repos/${REPO}/pulls -f head=${branch} -f base=main -f title=${JSON.stringify(title)} -F body=@${bodyFile}`));
  console.log(`opened PR #${pr.number}`);
} else console.log(`reusing open PR #${pr.number}`);

for (let i = 0; ; i++) {
  const p = api(`pulls/${pr.number}`);
  if (p.mergeable_state === 'clean') break;
  if (p.mergeable_state === 'dirty') die(`PR #${pr.number} has conflicts`);
  if (p.mergeable_state === 'blocked' || p.mergeable_state === 'unstable') {
    const runs = api(`commits/${p.head.sha}/check-runs`).check_runs;
    const failed = runs.filter((r) => r.conclusion && !['success', 'skipped', 'neutral'].includes(r.conclusion));
    if (failed.length) die(`check failed: ${failed.map((r) => `${r.name} (${r.html_url})`).join(', ')}`);
  }
  if (i > 120) die('waited 20 minutes for the check job');
  await sleep(10);
}
const m = JSON.parse(sh(`gh api -X PUT repos/${REPO}/pulls/${pr.number}/merge -f merge_method=merge`));
if (!m.merged) die(`merge refused: ${m.message}`);
console.log(`merged PR #${pr.number} → ${m.sha}`);

for (let i = 0; ; i++) {
  const r = api(`actions/runs?branch=main&head_sha=${m.sha}`).workflow_runs.find((w) => /deploy/i.test(w.name));
  if (r?.status === 'completed') { if (r.conclusion !== 'success') die(`deploy ${r.conclusion}: ${r.html_url}`); console.log(`deployed: ${r.html_url}`); break; }
  if (i > 90) die('deploy did not finish in 15 minutes');
  await sleep(10);
}
run('git fetch origin');
run('git merge --ff-only origin/main');
run(`git push origin ${branch}`);
console.log(`\n✓ Task ${task} is live (PR #${pr.number}). Mark it ✅ in the work list with today's date.`);
