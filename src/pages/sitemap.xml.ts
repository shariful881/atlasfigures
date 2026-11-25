// XML sitemap: only indexable, canonical pages. Add every new indexable page here
// with the date its content last changed (not the build date).
import { abs } from '../site';

const pages: { path: string; lastmod: string }[] = [
  { path: '/', lastmod: '2026-11-25' },
  { path: '/population/', lastmod: '2026-11-25' },
  { path: '/population/bangladesh/', lastmod: '2026-11-25' },
  { path: '/about/', lastmod: '2026-11-25' },
  { path: '/methodology/', lastmod: '2026-11-25' },
  { path: '/sources/', lastmod: '2026-11-25' },
  { path: '/corrections/', lastmod: '2026-11-25' },
  { path: '/contact/', lastmod: '2026-11-25' },
  { path: '/privacy/', lastmod: '2026-11-25' },
];

export function GET() {
  const urls = pages.map((p) => `  <url><loc>${abs(p.path)}</loc><lastmod>${p.lastmod}</lastmod></url>`).join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls}\n</urlset>\n`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
