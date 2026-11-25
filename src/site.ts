// Site-wide constants and helpers for URLs and structured data.
export const SITE_NAME = 'AtlasFigures';
export const SITE_TAGLINE = 'Every country, told on its own terms.';
export const PUBLISHER = 'AtlasFigures Editorial';

const base = import.meta.env.BASE_URL.replace(/\/$/, '');
const siteUrl = (import.meta.env.SITE as string | undefined)?.replace(/\/$/, '') ?? '';

/** Path inside the site, respecting the deploy base (e.g. /atlasfigures). */
export const path = (p: string) => `${base}${p.startsWith('/') ? p : `/${p}`}`;
/** Absolute URL for canonical tags and JSON-LD. */
export const abs = (p: string) => `${siteUrl}${path(p)}`;

export const ORG_ID = abs('/#organization');
export const WEBSITE_ID = abs('/#website');

export const organization = () => ({
  '@type': 'Organization',
  '@id': ORG_ID,
  name: SITE_NAME,
  url: abs('/'),
  logo: { '@type': 'ImageObject', url: abs('/icon-512.png'), width: 512, height: 512 },
  description: 'Population, time, economy and country rankings for every country, with every figure sourced.',
});

export const website = () => ({
  '@type': 'WebSite',
  '@id': WEBSITE_ID,
  name: SITE_NAME,
  url: abs('/'),
  publisher: { '@id': ORG_ID },
  inLanguage: 'en',
});

export type Crumb = { name: string; href: string };
export const breadcrumbList = (crumbs: Crumb[]) => ({
  '@type': 'BreadcrumbList',
  itemListElement: crumbs.map((c, i) => ({ '@type': 'ListItem', position: i + 1, name: c.name, item: abs(c.href) })),
});

/** Human-readable date, e.g. "25 November 2026". */
export const longDate = (iso: string) =>
  new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });

/** Public issue tracker, used for error reports until the owner sets a contact email. */
export const ISSUES_URL = 'https://github.com/shariful881/atlasfigures/issues';
/** Pre-filled "report an error" form for one page. */
export const reportErrorUrl = (pageName: string, pagePath: string) =>
  `${ISSUES_URL}/new?title=${encodeURIComponent(`Error on: ${pageName}`)}&body=${encodeURIComponent(
    `Page: ${abs(pagePath)}\n\nWhat is wrong:\n\nWhat it should say, with a link to the source:\n`,
  )}`;

/** Trust pages, in the order they appear in the footer and on the mobile "More" page. */
export const INFO_LINKS: { label: string; href: string; text: string }[] = [
  { label: 'About AtlasFigures', href: '/about/', text: 'Who makes this site and how' },
  { label: 'Methodology', href: '/methodology/', text: 'How figures and live counters are made' },
  { label: 'Sources', href: '/sources/', text: 'Every data source we use' },
  { label: 'Corrections', href: '/corrections/', text: 'How we fix errors, and what we fixed' },
  { label: 'Contact', href: '/contact/', text: 'Questions and suggestions' },
  { label: 'Privacy', href: '/privacy/', text: 'What we collect and why' },
];
