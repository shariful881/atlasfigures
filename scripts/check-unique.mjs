// Uniqueness check: no two country pages may share wording.
// Run after `astro build`:  node scripts/check-unique.mjs [distDir]
// The rules (what is compared, what counts as the same wording) live in scripts/lib/unique-core.mjs.
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { loadPages } from './lib/unique-core.mjs';

const DIST = process.argv[2] || 'dist';
if (!existsSync(join(DIST, 'population'))) { console.error(`No ${join(DIST, 'population')}. Run the build first.`); process.exit(2); }

const pages = loadPages(DIST);

let problems = 0;
for (let i = 0; i < pages.length; i++) {
  for (let j = i + 1; j < pages.length; j++) {
    const a = pages[i], b = pages[j];
    const shared = [...a.grams.keys()].filter((g) => b.grams.has(g));
    const heads = [...a.heads.keys()].filter((h) => b.heads.has(h));
    if (!shared.length && !heads.length) continue;
    console.log(`\n✗ ${a.slug} ↔ ${b.slug}`);
    for (const h of heads) { console.log(`  same heading: "${a.heads.get(h)}"  ↔  "${b.heads.get(h)}"`); problems++; }
    const seen = new Set();
    for (const g of shared) {
      const s = a.grams.get(g);
      if (seen.has(s)) continue; seen.add(s);
      console.log(`  shared wording "${g}"\n    in: "${s.slice(0, 140)}"`); problems++;
    }
  }
}

console.log(`\nChecked ${pages.length} country page(s).`);
if (problems) { console.log(`${problems} problem(s): rewrite these so each page says it in its own words.`); process.exit(1); }
console.log('✓ Every country page is written in its own words.');
