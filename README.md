# AtlasFigures

World population, time, economy and country rankings — every country told on its own terms.

- Framework: [Astro](https://astro.build), static output
- Staging: GitHub Pages at https://shariful881.github.io/atlasfigures/ (noindex)
- Launch: Cloudflare Pages at https://atlasfigures.com

## Rules

1. **No content templates.** Each country page is its own file in `src/pages/<section>/<country>.astro`, written around that country's story.
2. **Same design everywhere.** Pages use the shared `Base` layout and components in `src/components/` (Key Facts box, live counter, charts).
3. **Every number is sourced.** Data lives in `src/data/countries/<country>.json` with its source.

## Develop

```bash
npm install
npm run dev
```

## Moving to atlasfigures.com (Cloudflare Pages)

Build command `npm run build`, output `dist`, with environment variables:

```
SITE_URL=https://atlasfigures.com
SITE_BASE=/
PUBLIC_INDEXABLE=true
```

Then delete `public/robots.txt`'s `Disallow: /` line so search engines can crawl.
