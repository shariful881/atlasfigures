// @ts-check
import { defineConfig } from 'astro/config';

// While the site lives on GitHub Pages (shariful881.github.io/atlasfigures),
// SITE_BASE is "/atlasfigures". When we move to atlasfigures.com on Cloudflare,
// set SITE_URL=https://atlasfigures.com and SITE_BASE=/ — no code changes needed.
export default defineConfig({
  site: process.env.SITE_URL || 'https://shariful881.github.io',
  base: process.env.SITE_BASE || '/atlasfigures',
  trailingSlash: 'ignore',
});
