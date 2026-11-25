// Shared access to the generated UN data (src/data/wpp/, built by scripts/build-data.mjs from the
// original UN files) and the site's number style (data guide §4). Pages never type figures by hand.
import index from '../data/wpp/index.json';
import world from '../data/wpp/world.json';

export type Year = {
  year: number; projection: boolean; population: number; densityPerKm2: number; growthRatePct: number;
  change: number; netMigrants: number; fertility: number; medianAge: number; lifeExpectancy: number;
  urbanPct: number | null; worldRank: number | null; worldSharePct: number;
};
export type CountryData = {
  meta: any; unName: string; locId: number; iso3: string; iso2: string; region: string; subregion: string;
  landAreaKm2: number; years: Year[];
};

const files = import.meta.glob<CountryData>('../data/wpp/countries/*.json', { eager: true, import: 'default' });
export function countryData(iso3: string): CountryData {
  const d = files[`../data/wpp/countries/${iso3}.json`];
  if (!d) throw new Error(`No UN data for ${iso3}`);
  return d;
}
export const worldData = world as unknown as { meta: any; years: Year[] };
export const countryIndex = index as unknown as { year: number; worldPopulation: number; countries: { iso3: string; unName: string; population: number; densityPerKm2: number; worldRank: number }[] };

export const CURRENT_YEAR = 2026;
/** Year rows by year number. */
export const byYear = (years: Year[]) => Object.fromEntries(years.map((y) => [y.year, y])) as Record<number, Year>;

// ---------- number style (data guide §4) ----------
const r = (v: number, d: number) => Number(v.toFixed(d));
/** Whole number with commas: 1,366 */
export const int = (v: number) => Math.round(v).toLocaleString('en-US');
/** Fixed decimals for display: dec(2.0899, 2) → "2.09" */
export const dec = (v: number, d: number) => r(v, d).toFixed(d);
/** Prose millions, 1 decimal: "177.8 million" */
export const millions = (v: number) => `${(v / 1e6).toFixed(1)} million`;
/** Short millions for tiles: "177.8M" */
export const millionsShort = (v: number) => `${(v / 1e6).toFixed(1)}M`;
/** Prose billions, 1 decimal: "8.3 billion" */
export const billions = (v: number) => `${(v / 1e9).toFixed(1)} billion`;
/** Percent, 1 decimal: "1.2%" */
export const pct = (v: number) => `${v.toFixed(1)}%`;
/** Ordinal: 8 → "8th" */
export const ord = (n: number) => {
  const s = ['th', 'st', 'nd', 'rd'], v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

/** Rows for charts/tables, rounded the way they are shown. */
export function displayRows(years: Year[], pick: number[]) {
  const y = byYear(years);
  return pick.map((yr) => {
    const v = y[yr];
    if (!v) throw new Error(`No data for ${yr}`);
    return {
      year: yr,
      projection: v.projection,
      population: v.population,
      density: Math.round(v.densityPerKm2),
      fertility: r(v.fertility, 2),
      medianAge: r(v.medianAge, 1),
      urbanPct: v.urbanPct == null ? null : r(v.urbanPct, 1),
      netMigrants: v.netMigrants,
      rank: v.worldRank,
    };
  });
}

/** Fails the build if a sentence on a page would no longer be true for the data. */
export function assertClaim(ok: boolean, claim: string) {
  if (!ok) throw new Error(`Page claim no longer true for the UN data: ${claim}`);
}
