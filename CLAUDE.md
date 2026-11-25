# AtlasFigures — rules for every change

Full guides live in the claude.ai Project "World Meters":
`claude/atlasfigures-plan.md`, `claude/atlasfigures-design-guide.md`, `claude/atlasfigures-seo-guide.md`.
Every new page, section or change must follow all three. Summary:

## Content
- No content templates. Each country/topic page is its own `.astro` file written around that place's own story.
- Every number has a source; numbers in JSON-LD must equal numbers on the page.
- Page order: H1 → live counter (if relevant) → 1–2 sentence direct answer → Key facts → story sections
  (H2 phrased as the question people search, first sentence answers it) → charts (same numbers also in an HTML table)
  → yearly table + CSV download → Quick answers (FAQ) → Sources and methodology.
- Sources section is ALWAYS a collapsed `<details>` accordion (like FAQ) on desktop and mobile, containing
  the source list, methodology link and Published/Updated dates.
- Projections are always labelled "UN projection".

## Design (two designs, one URL)
- < 768px: mobile app shell (app bar, bottom tab bar, segment tabs, bottom sheets). >= 768px: website layout.
- Same content on both; mobile may fold content (tabs/sheets), never drop it.
- Use the shared layout `src/layouts/Base.astro` and components in `src/components/`.

## SEO
- Pass `breadcrumbs` and `schema` to `Base` (it adds Organization + WebSite + BreadcrumbList). Show Published/Updated dates on the page and use the same dates in the Article schema. Add every indexable page to `src/pages/sitemap.xml.ts`.
- Country pages: Article + about Country + Dataset (with real CSV) + FAQPage. Hubs: CollectionPage + ItemList.
  Time/city pages: WebPage + about City. Never Event schema for holidays; never schema for content not shown.
- Thin or "coming soon" pages: `noindex`. Staging (github.io) is noindex until launch on atlasfigures.com.
- Do not add llms.txt, chunked "AI" pages, or nosnippet.
- Before publishing: build, check JSON-LD, Lighthouse mobile ≥ 90 (Performance/SEO/Accessibility), screenshots at 1280px and 390px.
