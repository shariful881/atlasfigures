// Common English names for every country or area (data guide §5: titles and lists use the name people search
// for; the UN's official name stays in Key facts/Sources). Order of precedence:
//   1. the editorial JSON of a country page (src/data/countries/, src/data/economy/) — what the page itself uses
//   2. NAMES below — short forms for UN names that are long or formal
//   3. the UN WPP name as published
// Disputed areas keep neutral wording ("country or area"); see the data guide.
import wpp from '../data/wpp/index.json';
import commonNames from '../data/common-names.json';

const NAMES: Record<string, string> = commonNames.names;

const editorial = Object.values({
  ...import.meta.glob('../data/countries/*.json', { eager: true, import: 'default' }),
  ...import.meta.glob('../data/economy/*.json', { eager: true, import: 'default' }),
}) as { iso3: string; name: string; slug: string }[];
const fromPages = new Map(editorial.map((c) => [c.iso3, c.name]));
const unNames = new Map((wpp as any).countries.map((c: any) => [c.iso3, c.unName]));
const unMeta = new Map((wpp as any).countries.map((c: any) => [c.iso3, c]));

export function commonName(iso3: string): string {
  return fromPages.get(iso3) ?? NAMES[iso3] ?? (unNames.get(iso3) as string) ?? iso3;
}
/** UN's official name, when it differs from the common name. */
export const unName = (iso3: string) => (unNames.get(iso3) as string | undefined) ?? null;
/** ISO alpha-2 (lower case) from the UN file, for flags. */
export const iso2 = (iso3: string) => ((unMeta.get(iso3) as any)?.iso2 as string | undefined)?.toLowerCase() ?? null;

const popPages = new Set((Object.values(import.meta.glob('../data/countries/*.json', { eager: true, import: 'default' })) as any[]).map((c) => `${c.iso3}|${c.slug}`));
const econPages = new Set((Object.values(import.meta.glob('../data/economy/*.json', { eager: true, import: 'default' })) as any[]).map((c) => `${c.iso3}|${c.slug}`));
const slugOf = (set: Set<string>, iso3: string) => [...set].find((x) => x.startsWith(`${iso3}|`))?.split('|')[1] ?? null;
/** Site paths of the country's own pages, if they exist. */
export const pagesOf = (iso3: string) => ({
  population: slugOf(popPages, iso3) ? `/country/${slugOf(popPages, iso3)}/population/` : null,
  economy: slugOf(econPages, iso3) ? `/country/${slugOf(econPages, iso3)}/economy/` : null,
});
