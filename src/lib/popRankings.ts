// Population rankings (task 21): every country or area in UN World Population Prospects 2024, one year at a time.
// Used by the ranking pages and their CSV files, so page, CSV and JSON-LD always come from the same list.
// Every figure comes from src/data/wpp/ (generated from the original UN files); nothing is typed by hand.
import index from '../data/wpp/index.json';
import { CURRENT_YEAR, type Year } from './figures';
import { commonName, pagesOf } from './names';

const files = import.meta.glob('../data/wpp/countries/*.json', { eager: true, import: 'default' }) as Record<string, any>;
const byIso = new Map(Object.values(files).map((d: any) => [d.iso3, d]));
const meta = (index as any).countries as { iso3: string; region: string; subregion: string }[];

export type PopEntry = {
  rank: number; iso3: string; name: string; region: string; subregion: string; site: string | null;
  now: Year; landAreaKm2: number; yearOf: (y: number) => Year;
};

function entries(): Omit<PopEntry, 'rank'>[] {
  return meta.map((m) => {
    const d = byIso.get(m.iso3);
    const yr = new Map(d.years.map((r: Year) => [r.year, r]));
    const pg = pagesOf(m.iso3);
    return {
      iso3: m.iso3, name: commonName(m.iso3), region: m.region, subregion: m.subregion, site: pg.population,
      now: yr.get(CURRENT_YEAR) as Year, landAreaKm2: d.landAreaKm2, yearOf: (y: number) => yr.get(y) as Year,
    };
  });
}

/** All countries or areas ranked by mid-year population (largest first). */
export const byPopulation = (): PopEntry[] =>
  entries().sort((a, b) => b.now.population - a.now.population).map((e, i) => ({ ...e, rank: i + 1 }));

/** All countries or areas ranked by people per km² of land (most crowded first). */
export const byDensity = (): PopEntry[] =>
  entries().sort((a, b) => b.now.densityPerKm2 - a.now.densityPerKm2).map((e, i) => ({ ...e, rank: i + 1 }));

/** Rank a list by any year's population (used for 1950/2050 comparisons). */
export const rankIn = (list: PopEntry[], y: number) =>
  [...list].sort((a, b) => b.yearOf(y).population - a.yearOf(y).population);

export const UN_REGIONS = ['Africa', 'Asia', 'Europe', 'Latin America and the Caribbean', 'Northern America', 'Oceania'];
