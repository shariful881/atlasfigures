// robots.txt: closed on staging (github.io), open with sitemap on launch (PUBLIC_INDEXABLE=true).
import { abs } from '../site';
export function GET() {
  const open = import.meta.env.PUBLIC_INDEXABLE === 'true';
  const body = open
    ? `User-agent: *\nAllow: /\n\nSitemap: ${abs('/sitemap.xml')}\n`
    : `# Staging copy: kept out of search until launch on atlasfigures.com\nUser-agent: *\nDisallow: /\n`;
  return new Response(body, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
