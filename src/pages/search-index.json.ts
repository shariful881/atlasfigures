// Search index (task 7): every page a visitor can search for, built at build time from the same editorial JSON and
// ranking catalog the pages use. Loaded by the search box only when someone opens it, so pages stay light.
// Fields: t = title, s = subtitle, u = site path (with base), f = flag image URL, k = kind, a = other names to match.
import { path, INFO_LINKS } from '../site';
import { rankingCards } from '../lib/catalog';
import { countryData } from '../lib/figures';
import { econData } from '../lib/econ';
import { unName } from '../lib/names';

const flags = import.meta.glob('/node_modules/flag-icons/flags/4x3/*.svg', { eager: true, query: '?url&no-inline', import: 'default' }) as Record<string, string>;
const flagUrl = (code?: string | null) => (code ? Object.entries(flags).find(([p]) => p.endsWith(`/${code}.svg`))?.[1] ?? null : null);

type Entry = { t: string; s: string; u: string; f?: string | null; k: string; a?: string[] };

export function GET() {
  const pop = Object.values(import.meta.glob('../data/countries/*.json', { eager: true, import: 'default' })) as any[];
  const eco = Object.values(import.meta.glob('../data/economy/*.json', { eager: true, import: 'default' })) as any[];
  const aliases = (c: any) => [unName(c.iso3), c.iso3, c.demonym, c.capital].filter((x): x is string => Boolean(x) && x !== c.name);

  const entries: Entry[] = [
    { t: 'World population', s: 'Live counter and UN projections', u: path('/population/world/'), f: null, k: 'world', a: ['Earth', 'global population', 'world'] },
    ...pop.sort((a, b) => a.name.localeCompare(b.name)).map((c) => ({
      t: c.name, s: `Population · ${countryData(c.iso3).subregion}`, u: path(`/population/${c.slug}/`), f: flagUrl(c.code), k: 'population', a: aliases(c),
    })),
    ...eco.sort((a, b) => a.name.localeCompare(b.name)).map((c) => ({
      t: c.name, s: `Economy · ${econData(c.iso3).region}`, u: path(`/economy/${c.slug}/`), f: flagUrl(c.code), k: 'economy', a: aliases(c),
    })),
    ...rankingCards().map((r) => ({ t: r.title, s: `Ranking · ${r.count} ranked · ${r.year}`, u: path(r.href), f: null, k: 'ranking', a: [r.blurb] })),
    { t: 'Population by country', s: 'Section · every country page', u: path('/population/'), f: null, k: 'section' },
    { t: 'Economy by country', s: 'Section · every country page', u: path('/economy/'), f: null, k: 'section' },
    { t: 'Country rankings', s: 'Section · every ranking', u: path('/rankings/'), f: null, k: 'section' },
    ...INFO_LINKS.map((l) => ({ t: l.label, s: l.text, u: path(l.href), f: null, k: 'info' })),
  ];
  return new Response(JSON.stringify(entries), { headers: { 'Content-Type': 'application/json' } });
}
