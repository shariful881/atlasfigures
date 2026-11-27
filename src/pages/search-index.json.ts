// Search index (task 7): every page a visitor can search for, built at build time from the same editorial JSON and
// ranking catalog the pages use. Loaded by the search box only when someone opens it, so pages stay light.
// Fields: t = title, s = subtitle, u = site path (with base), f = flag image URL, k = kind, a = other names to match.
import { path, INFO_LINKS } from '../site';
import { rankingCards } from '../lib/catalog';
import { countryData } from '../lib/figures';
import { econData } from '../lib/econ';
import { unName } from '../lib/names';
import countryList from '../data/country-list.json';

const flags = import.meta.glob('/node_modules/flag-icons/flags/4x3/*.svg', { eager: true, query: '?url&no-inline', import: 'default' }) as Record<string, string>;
const flagUrl = (code?: string | null) => (code ? Object.entries(flags).find(([p]) => p.endsWith(`/${code}.svg`))?.[1] ?? null : null);

type Entry = { t: string; s: string; u: string; f?: string | null; k: string; a?: string[] };

export function GET() {
  const pop = Object.values(import.meta.glob('../data/countries/*.json', { eager: true, import: 'default' })) as any[];
  const eco = Object.values(import.meta.glob('../data/economy/*.json', { eager: true, import: 'default' })) as any[];
  const cities = Object.values(import.meta.glob('../data/cities/*.json', { eager: true, import: 'default' })) as any[];
  const aliases = (c: any) => [unName(c.iso3), c.iso3, c.demonym, c.capital].filter((x): x is string => Boolean(x) && x !== c.name);

  const entries: Entry[] = [
    { t: 'World population', s: 'Live counter and UN projections', u: path('/population/world/'), f: null, k: 'world', a: ['Earth', 'global population', 'world'] },
    ...pop.sort((a, b) => a.name.localeCompare(b.name)).map((c) => ({
      t: c.name, s: `Population · ${countryData(c.iso3).subregion}`, u: path(`/country/${c.slug}/population/`), f: flagUrl(c.code), k: 'population', a: aliases(c),
    })),
    ...eco.sort((a, b) => a.name.localeCompare(b.name)).map((c) => ({
      t: c.name, s: `Economy · ${econData(c.iso3).region}`, u: path(`/country/${c.slug}/economy/`), f: flagUrl(c.code), k: 'economy', a: aliases(c),
    })),
    ...cities.sort((a, b) => a.name.localeCompare(b.name)).map((c) => ({
      t: `Time in ${c.name}`, s: `Time · ${c.country}`, u: path(`/time/${c.slug}/`), f: flagUrl(c.code), k: 'time', a: [c.name, c.country, c.tz, 'time', 'clock'],
    })),
    ...rankingCards().map((r) => ({ t: r.title, s: `Ranking · ${r.count} ranked · ${r.year}`, u: path(r.href), f: null, k: 'ranking', a: [r.blurb] })),
    { t: 'All countries and areas, A–Z', s: `Section · all ${countryList.count} in the UN list`, u: path('/country/'), f: null, k: 'section', a: ['countries', 'country list', 'all countries', 'list of countries', 'territories'] },
    { t: 'Population by country', s: 'Section · every country page', u: path('/population/'), f: null, k: 'section' },
    { t: 'Economy by country', s: 'Section · every country page', u: path('/economy/'), f: null, k: 'section' },
    ...(Object.values(import.meta.glob('../data/pairs/*.json', { eager: true, import: 'default' })) as any[]).map((pr) => {
      const A = cities.find((c) => c.slug === pr.a), B = cities.find((c) => c.slug === pr.b);
      return { t: `${A.name} to ${B.name} time`, s: 'Time difference', u: path(`/time/${pr.slug}/`), f: null, k: 'time', a: [A.name, B.name, 'time difference', `${A.name} ${B.name}`] };
    }),
    { t: 'Bangladesh public holidays 2027', s: 'Holidays · all 29 dates', u: path('/holidays/bangladesh/2027/'), f: null, k: 'time', a: ['holiday', 'holidays', 'chuti', 'Eid', 'Bangladesh', 'public holiday', '2027'] },
    { t: 'Eid-ul-Fitr 2027 countdown', s: 'Countdown · Bangladesh', u: path('/countdown/eid-ul-fitr/'), f: null, k: 'time', a: ['Eid', 'Eid ul Fitr', 'Ramadan', 'countdown', 'Bangladesh'] },
    { t: 'Time zone converter', s: 'Tool · convert a time between cities', u: path('/time/converter/'), f: null, k: 'section', a: ['converter', 'time zone', 'convert time'] },
    { t: 'World clock', s: 'Section · local time in major cities', u: path('/time/'), f: null, k: 'section', a: ['time', 'clock', 'time zone'] },
    { t: 'Country rankings', s: 'Section · every ranking', u: path('/rankings/'), f: null, k: 'section' },
    ...INFO_LINKS.map((l) => ({ t: l.label, s: l.text, u: path(l.href), f: null, k: 'info' })),
  ];
  return new Response(JSON.stringify(entries), { headers: { 'Content-Type': 'application/json' } });
}
