# AtlasFigures — rules for every change

## ⚠️ Going live (owner's rule — never skip)
- Never publish directly. Pushing to `main` deploys the live site, so work ONLY on the `dev` branch.
- When work is done: show the owner what changed (screenshots at 1280px and 390px + a short list). Do not merge.
- Merge `dev` → `main` (go live) ONLY after the owner explicitly says to make it live. One approval covers only that piece of work.
- `main` is protected by a GitHub ruleset ("Protect main (live site)"): no direct pushes, no force push, no deletion;
  changes reach `main` only through a pull request from `dev`, and the `check` job must pass first.

## Tools: no laptop needed for normal work
- Push, pull requests, merges, CI status: do it from this workspace with `git` and `gh api` (authenticated as
  shariful881; ignore `gh auth status` saying the token is invalid). Example go-live:
  `gh api repos/shariful881/atlasfigures/pulls -f head=dev -f base=main -f title=... -f body=...` then
  `gh api -X PUT repos/shariful881/atlasfigures/pulls/<n>/merge` after the `check` job passed.
- UN data downloads: the "Fetch UN data (dev)" workflow. Screenshots/Lighthouse: Playwright + local Chrome here.
- The owner's laptop (Chrome) only for things that need the owner's own login: domain/Cloudflare, Search Console,
  AdSense, GitHub identity prompts. Tell the owner beforehand so the laptop is on.

## Work list (owner's rule)
- All tasks are numbered in the Project doc `claude/atlasfigures-worklist.md`. Do ONLY the task number the owner
  names, one at a time; never start the next one on your own. When done: call the owner (changes + screenshots),
  ask whether to make it live, mark it 👀, and propose the next task number with a one-line reason. Wait.
  After "live koro" → PR dev → main, merge, mark ✅ with the date. Update the work list after every task.

Full guides live in the claude.ai Project "World Meters":
`claude/atlasfigures-plan.md`, `claude/atlasfigures-design-guide.md`, `claude/atlasfigures-components-guide.md`,
`claude/atlasfigures-seo-guide.md`, `claude/atlasfigures-data-guide.md`.
Every new page, section or change must follow all of them. Summary:

## Content
- No content templates. Each country/topic page is its own `.astro` file written around that place's own story.
- **No two country pages may share wording (owner's rule).** Not a sentence, not a heading, not an FAQ question,
  not the title or meta description — even with the country name and numbers swapped. Each page picks its own
  story sections, its own question headings (from what people actually search about that country), its own
  FAQ questions and its own chart/table titles. Only fixed site UI (live counter, Key facts labels, tabs,
  table cells, badges, the Sources accordion's citations, header/footer) may repeat.
- Enforced by `npm run check` (build + `scripts/check-unique.mjs`, also run by CI on `dev`). A page that fails
  is rewritten, never published. Country JSON must have `name`, `demonym` and `capital` for the check.
- Every number has a source; numbers in JSON-LD must equal numbers on the page.
- Page order: H1 → live counter (if relevant) → 1–2 sentence direct answer → Key facts → story sections
  (H2 phrased as the question people search, first sentence answers it) → charts (same numbers also in an HTML table)
  → yearly table + CSV download → Quick answers (FAQ) → Sources and methodology.
- Sources section is ALWAYS a collapsed `<details>` accordion (like FAQ) on desktop and mobile, containing
  the source list, methodology link and Published/Updated dates.
- Projections are always labelled "UN projection".
- FAQ: every question starts CLOSED (no `open` attribute), desktop and mobile.
- "Verified" badge (`SourceBadge` with `checkedOn`) only after the figures were actually checked against the
  named source; record the check in the country JSON under `verification` (date, what was checked, against what).
  Without a check, pass no `checkedOn` (plain "Source:" line, no badge).

## Google safety (spam / AI-content policies)
- Before publishing, check every claim and number by hand against the source, INCLUDING title, meta description,
  JSON-LD and image alt text (Google generative-AI guidance, Oct 2026). Record it in `verification`
  (`checkedOn`, `checkedBy`, `what`, `against`).
- Every page has at least one section that is only about that country. Publish slowly: 3–5 countries a day.
- Dates: Published never changes. Updated changes only for real changes (new data, new/rewritten section,
  correction), never for typos/style/code. Updated = Article dateModified = sitemap lastmod. Log the reason in
  the country JSON `changelog`.
- During a Google core update, don't react to ranking moves; wait until rollout ends + 1 week.

## Data
- No hand-typed numbers in `.astro`. Original UN files live in `data/raw/un-wpp-2024/` (fetched by the
  "Fetch UN data (dev)" workflow; `SOURCE.md` has URLs, download date, SHA-256). `scripts/build-data.mjs`
  (`npm run data`, also runs automatically before every build) turns them into `src/data/wpp/` — `world.json`,
  `index.json`, `countries/<ISO3>.json` (1950–2100, `projection` flag, rank and world share per year). These are
  generated, git-ignored, never edited by hand. `src/data/countries/<slug>.json` holds only editorial fields
  (name, demonym, capital, iso3, verification, changelog) and pages take every figure from `src/data/wpp/`.
  The UN interim update (19 Jan 2026, Togo) replaces the original rows. TODO: number test page = JSON = JSON-LD.
- New UN WPP revision → update and re-verify ALL pages together. Current: WPP 2024.
- Number style: prose millions 1 decimal ("177.8 million"), billions 1–2 decimals, percent 1 decimal, density
  whole number; tables/Key facts/CSV full numbers with commas; dates "25 November 2026".
- Country list per UN WPP; titles/H1/URL use the common English name, UN official name in Key facts/Sources.
  Disputed areas: neutral factual wording, "country or area", no side taken.
- Every live counter shows "Estimate based on UN projections".

## Ads & privacy (before AdSense goes on)
- Google-certified IAB TCF CMP for EEA/UK/Switzerland; Privacy policy updated.
- Ad slots reserve their height (CLS ≤ 0.1); never before H1/live counter/direct answer; mobile max one ad per
  screen, between cards; no sticky ads over the tab bar/app bar.
- Analytics: cookieless only (Cloudflare Web Analytics). No other tracking without the owner's OK.

## Quality
- URLs never change once published (301 via Cloudflare only if unavoidable, after launch).
- Each country page links to its hub, 3–5 same-region countries that have pages, and related rankings; no orphans.
- "Report an error" link in every Sources accordion + a Corrections policy page (in footer).

## Components (use these, don't hand-roll)
- `LiveCounter`: LIVE pill + local clock, rolling odometer digits, "Next +1" progress bar, today / this year / per day.
- `KeyFacts`: titled "<Country> at a glance" card with flag and grouped rows (People / Land / Society);
  mobile = titled tiles + bottom sheet. Verified badge in the footer.
- `LineChart`: title, subtitle, legend, area fill, labelled first / now / last points, dashed UN projection band,
  optional reference line, hover/touch readout, verified badge footer. Separate desktop and mobile SVGs.
- `DataTable`: titled card, CSV button, inline population bars, "Now" row highlight, "UN projections" band,
  verified badge + licence footer.
- Tabular figures only in table cells and the odometer; never on numbers containing "." inside running text or chips.

## Design (two designs, one URL)
- < 768px: mobile app shell (app bar, bottom tab bar, segment tabs, bottom sheets). >= 768px: website layout.
- Same content on both; mobile may fold content (tabs/sheets), never drop it.
- Use the shared layout `src/layouts/Base.astro` and components in `src/components/`.

## SEO
- Pass `breadcrumbs` and `schema` to `Base` (it adds Organization + WebSite + BreadcrumbList). Show Published/Updated dates on the page and use the same dates in the Article schema. Add every indexable page to `src/pages/sitemap.xml.ts`.
- Country pages: Article + about Country + Dataset (with real CSV) + FAQPage. Hubs: CollectionPage + ItemList.
  Time/city pages: WebPage + about City. Never Event schema for holidays; never schema for content not shown.
- JSON-LD dates are full ISO datetimes with time zone (e.g. 2026-11-25T12:00:00+06:00). UN WPP data licence = CC BY 3.0 IGO (verified); add `license` to Dataset only when verified.
- Thin or "coming soon" pages: `noindex`. Staging (github.io) is noindex until launch on atlasfigures.com.
- Do not add llms.txt, chunked "AI" pages, or nosnippet.
- Before publishing: `npm run check` (build + uniqueness), check JSON-LD, Lighthouse mobile ≥ 90 (Performance/SEO/Accessibility), screenshots at 1280px and 390px.
