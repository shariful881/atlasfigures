# AtlasFigures — rules for every change

## ⚠️ Going live (owner's rule — never skip)
- Never publish directly. Pushing to `main` deploys the live site, so work ONLY on the `dev` branch.
- When work is done: show the owner what changed (screenshots at 1280px and 390px + a short list). Do not merge.
- Merge `dev` → `main` (go live) ONLY after the owner explicitly says to make it live. One approval covers only that piece of work.

Full guides live in the claude.ai Project "World Meters":
`claude/atlasfigures-plan.md`, `claude/atlasfigures-design-guide.md`, `claude/atlasfigures-seo-guide.md`.
Every new page, section or change must follow all three. Summary:

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
- Before publishing: build, check JSON-LD, Lighthouse mobile ≥ 90 (Performance/SEO/Accessibility), screenshots at 1280px and 390px.
