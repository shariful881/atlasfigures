// National flags from flag-icons (MIT licence, https://github.com/lipis/flag-icons), 4:3 SVG files.
// Vite copies each file into the build; a page only downloads the flags it shows (lazy-loaded images).
import { iso2 } from './names';

const files = import.meta.glob('/node_modules/flag-icons/flags/4x3/*.svg', { eager: true, query: '?url&no-inline', import: 'default' }) as Record<string, string>;
const byCode = new Map(Object.entries(files).map(([p, url]) => [p.split('/').pop()!.replace('.svg', ''), url]));
const EXTRA: Record<string, string> = { XKX: 'xk' };

/** URL of the flag for an ISO3 code, or null when there is none (e.g. groupings such as the Channel Islands). */
export function flagUrl(iso3: string): string | null {
  const code = EXTRA[iso3] ?? iso2(iso3);
  return (code && byCode.get(code)) ?? null;
}
