// Related-country picks for every country page (task 6), computed once for the whole site so no page is left without inbound links.
// Rule per page: all same-subregion countries with a page (up to 5; the largest first as the regional anchor, then the closest in size),
// topped up to 5 from the same UN region the same way. Then an orphan pass: a page that no other page links to takes over the
// least-close region top-up slot (never a same-subregion slot, never the anchor) on the same-region page closest to it in size,
// as long as the country it replaces stays linked from somewhere else. If no page has a top-up slot to spare, the closest-sized
// same-region page with a single region slot gives that slot (its anchor) to the orphan, again only if the anchor stays linked elsewhere.
import index from '../data/wpp/index.json';

const pageCountries = Object.values(import.meta.glob('../data/countries/*.json', { eager: true, import: 'default' })) as any[];
const all = (index as any).countries as any[];
const MAX = 5;

type Entry = { iso3: string; un: any; page: any };
const entries: Entry[] = pageCountries
  .map((p) => ({ iso3: p.iso3, page: p, un: all.find((c) => c.iso3 === p.iso3) }))
  .filter((e) => e.un)
  .sort((a, b) => a.iso3.localeCompare(b.iso3));

const gap = (a: Entry, b: Entry) => Math.abs(Math.log(a.un.population / b.un.population));
const anchored = (self: Entry, list: Entry[], n: number) => {
  if (!list.length || n <= 0) return [];
  const sorted = [...list].sort((a, b) => gap(a, self) - gap(b, self) || a.iso3.localeCompare(b.iso3));
  const anchor = [...list].sort((a, b) => b.un.population - a.un.population)[0];
  return [anchor, ...sorted.filter((p) => p !== anchor)].slice(0, n);
};

type Picks = { sub: Entry[]; region: Entry[] };
const picks = new Map<string, Picks>();
for (const self of entries) {
  const others = entries.filter((e) => e !== self);
  const sub = anchored(self, others.filter((e) => e.un.subregion === self.un.subregion), MAX);
  const region = anchored(self, others.filter((e) => e.un.region === self.un.region && e.un.subregion !== self.un.subregion), MAX - sub.length);
  picks.set(self.iso3, { sub, region });
}

const inbound = () => {
  const m = new Map<string, number>(entries.map((e) => [e.iso3, 0]));
  for (const p of picks.values()) for (const e of [...p.sub, ...p.region]) m.set(e.iso3, (m.get(e.iso3) ?? 0) + 1);
  return m;
};

for (const orphan of entries) {
  if ((inbound().get(orphan.iso3) ?? 0) > 0) continue;
  const hosts = entries
    .filter((h) => h !== orphan && h.un.region === orphan.un.region && h.un.subregion !== orphan.un.subregion && picks.get(h.iso3)!.region.length > 1)
    .sort((a, b) => gap(a, orphan) - gap(b, orphan) || a.iso3.localeCompare(b.iso3));
  for (const h of hosts) {
    const reg = picks.get(h.iso3)!.region;
    const counts = inbound();
    // the region anchor (index 0) stays; replace the least-close top-up whose country keeps another inbound link
    const idx = [...reg.keys()].slice(1).reverse().find((i) => (counts.get(reg[i].iso3) ?? 0) > 1);
    if (idx === undefined) continue;
    reg[idx] = orphan;
    break;
  }
  if ((inbound().get(orphan.iso3) ?? 0) > 0) continue;
  // fallback when every same-region host has only its anchor slot (e.g. Central Asia once Eastern Asia had five pages):
  // the closest-sized host gives its single region slot to the orphan, if that anchor stays linked from elsewhere
  const single = entries
    .filter((h) => h !== orphan && h.un.region === orphan.un.region && h.un.subregion !== orphan.un.subregion && picks.get(h.iso3)!.region.length === 1)
    .sort((a, b) => gap(a, orphan) - gap(b, orphan) || a.iso3.localeCompare(b.iso3));
  for (const h of single) {
    const reg = picks.get(h.iso3)!.region;
    if ((inbound().get(reg[0].iso3) ?? 0) < 2) continue;
    reg[0] = orphan;
    break;
  }
}

/** Related countries for a page, largest first, with their UN index row and editorial page data. */
export function relatedCountries(iso3: string) {
  const p = picks.get(iso3);
  if (!p) return [];
  return [...p.sub, ...p.region].sort((a, b) => b.un.population - a.un.population).map((e) => ({ ...e.page, un: e.un }));
}
