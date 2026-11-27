# Work tools (task 149)

Internal tools for building and updating pages faster without relaxing any rule in CLAUDE.md or the
Project guides. None of them changes a live page; every page still goes through `npm run check`, the
independent verify script, screenshots, and the owner's approval.

| Tool | What it does | Typical use |
|---|---|---|
| `find-facts.mjs` | Story-ready facts per country from the generated World Bank data — records, "highest since", runs of rises/falls, thresholds crossed, change since 1990/2000, world and regional place — each with the `assertClaim(...)` line (helpers in `src/lib/claims.ts`) and the matching verify line (`scripts/verify/_wdi.py`). | `node scripts/tools/find-facts.mjs DNK FIN HUN --out tmp/facts.md` |
| `phrase-check.mjs` | The uniqueness rules of `check-unique` applied to drafts **before** building: against every written page in the last build and between the drafts themselves. `--bank` lists every heading/FAQ question already taken. | `node scripts/tools/phrase-check.mjs src/pages/economy/denmark.astro src/pages/economy/finland.astro` |
| `new-ranking.mjs` | `indicator`/`indicators`: registers World Bank codes (indicator list, `LABELS`, `IndicatorKey`). `page`: scaffolds a ranking page wired to the data, CSV, checker, catalog card and sitemap; its text is marked WRITE and the build fails until it is written. | see the header of the file |
| `shots.mjs` | 1280px and 390px screenshots of a batch, one contact sheet per width, full-length samples. | `node scripts/tools/shots.mjs /economy/denmark/ /economy/finland/ --out shots/142` |
| `go-live.mjs` | The owner's go-live steps in one command (merge main → check → verify → push → PR → wait for `check` → merge → wait for deploy → fast-forward). Refuses without the owner's go-live words. | only after "live koro" |
| `check-sources.mjs` | Has any source a new version, or is any unreachable? Reads `data/sources.json`. Runs weekly in `.github/workflows/watch-sources.yml`. | `node scripts/tools/check-sources.mjs` |
| `fetch-file.sh` | Download one file from its main address, then backups of the same file; refuses error pages. For the new fetch workflows (tasks 150–157). | `fetch-file.sh -o out.csv --min-bytes 100000 --expect 'Area Code' URL1 URL2` |

## Data updates (weekly)
1. `watch-sources.yml` (Mondays) runs `check-sources.mjs`.
2. New version of a source with `"autoFetch": true` → new branch `data-update-YYYYMMDD` from main, the source's
   fetch workflow runs there, starts the Check job, and opens a pull request into main (or an issue if Actions
   may not open pull requests).
3. Anything needing a hand step (e.g. a new Global Carbon Project record, a new UN revision) or an unreachable
   source → one issue, "Data sources need attention".
4. Pages whose sentences no longer hold are fixed and re-verified; dates and changelog change only for real data
   changes. Then it goes live without waiting (owner's rule, 27 Nov 2026) and the owner gets the list of every
   changed live link to check.
5. A source that keeps failing keeps its current data. A backup address is added to `data/sources.json` only after
   a hand check that it serves the identical file; a different dataset is a new source and needs the owner's OK.
