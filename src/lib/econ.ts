// Shared access to the generated World Bank data (src/data/wdi/, built by scripts/build-wdi.mjs from the
// original World Bank files in data/raw/wdi/) and the number style for money (data guide §4).
// Pages never type figures by hand; every sentence that depends on the data gets an assertClaim (figures.ts).
import meta from '../data/wdi/meta.json';
import index from '../data/wdi/index.json';
import aggregates from '../data/wdi/aggregates.json';

export type IndicatorKey =
  | 'gdp' | 'gdpPerCapita' | 'gdpPerCapitaPpp' | 'gdpGrowthPct' | 'inflationPct'
  | 'unemploymentPct' | 'remittances' | 'remittancesPctGdp' | 'internetPct'
  | 'mobilePer100' | 'mobileSubs' | 'broadbandPer100'
  | 'under5Mortality' | 'infantMortality' | 'maternalMortality'
  | 'exports' | 'imports' | 'exportsPctGdp' | 'importsPctGdp';
/** [year, value] pairs, years ascending, only years the World Bank publishes a value for. */
export type Series = [number, number][];
export type EconData = {
  iso3: string; wbName: string; region: string; incomeGroup: string | null; notes: string | null;
  series: Record<IndicatorKey, Series>;
};

const files = import.meta.glob<EconData>('../data/wdi/countries/*.json', { eager: true, import: 'default' });
export function econData(iso3: string): EconData {
  const d = files[`../data/wdi/countries/${iso3}.json`];
  if (!d) throw new Error(`No World Bank data for ${iso3}`);
  return d;
}
export const hasEconData = (iso3: string) => Boolean(files[`../data/wdi/countries/${iso3}.json`]);
export const econMeta = meta as any;
export const econIndex = index as any;
/** World Bank aggregate (e.g. 'WLD' World, 'SAS' South Asia, 'LMC' Lower middle income). */
export function aggregate(code: string): { code: string; name: string; series: Record<IndicatorKey, Series> } {
  const a = (aggregates as any).aggregates.find((x: any) => x.code === code);
  if (!a) throw new Error(`No World Bank aggregate ${code}`);
  return a;
}

/** Value for one year, or null if the World Bank has none. */
export const valueIn = (s: Series, year: number) => s.find(([y]) => y === year)?.[1] ?? null;
/** Latest year with a value. */
export const latest = (s: Series) => (s.length ? { year: s.at(-1)![0], value: s.at(-1)![1] } : null);

// ---------- number style for money (data guide §4) ----------
/** Prose US dollars, large: "$456.3 billion", "$1.23 trillion", "$812.5 million" */
export function usd(v: number) {
  const a = Math.abs(v);
  if (a >= 1e12) return `$${(v / 1e12).toFixed(2)} trillion`;
  if (a >= 1e9) return `$${(v / 1e9).toFixed(1)} billion`;
  if (a >= 1e6) return `$${(v / 1e6).toFixed(1)} million`;
  return usdWhole(v);
}
/** Whole US dollars with commas (per person figures, tables): "$2,597" */
export const usdWhole = (v: number) => `${v < 0 ? '-' : ''}$${Math.round(Math.abs(v)).toLocaleString('en-US')}`;
/** International dollars (PPP), whole: "Int$10,154" */
export const intDollars = (v: number) => `Int$${Math.round(v).toLocaleString('en-US')}`;
/** Percent with 1 decimal, keeps the sign for growth: "+3.5%", "-1.2%" */
export const signedPct = (v: number) => {
  const r = Number(v.toFixed(1));
  return r === 0 ? '0.0%' : `${r > 0 ? '+' : ''}${r.toFixed(1)}%`;
};

// ---------- rankings ----------
export type Ranked = { rank: number; iso3: string; region: string; incomeGroup: string | null; value: number };
/** Every World Bank economy with a value for `year`, largest first. Economies without a value that year are not
 *  ranked (no carrying forward of older years); see `notRanked`. */
export function rankBy(key: IndicatorKey, year: number): Ranked[] {
  return Object.values(files)
    .map((d) => ({ iso3: d.iso3, region: d.region, incomeGroup: d.incomeGroup, value: valueIn(d.series[key], year) }))
    .filter((x): x is Omit<Ranked, 'rank'> => x.value != null)
    .sort((a, b) => b.value - a.value || a.iso3.localeCompare(b.iso3))
    .map((x, i) => ({ ...x, rank: i + 1 }));
}
/** Economies left out of a ranking for `year`, with their latest year (null = never published). */
export function notRanked(key: IndicatorKey, year: number) {
  return Object.values(files)
    .filter((d) => valueIn(d.series[key], year) == null)
    .map((d) => ({ iso3: d.iso3, latestYear: latest(d.series[key])?.year ?? null }))
    .sort((a, b) => a.iso3.localeCompare(b.iso3));
}
/** Latest year for which a ranking is complete enough: the newest year in which the World total has a value. */
export const rankingYear = (key: IndicatorKey) => latest(aggregate('WLD').series[key])!.year;
/** For indicators whose World total runs ahead of country data (ITU telecom series): the newest year in which at
 *  least `share` of the economies that ever report the series have a value. */
export function coverageYear(key: IndicatorKey, share = 0.8) {
  const counts = new Map<number, number>();
  for (const d of Object.values(files)) for (const [y] of d.series[key] ?? []) counts.set(y, (counts.get(y) ?? 0) + 1);
  const max = Math.max(...counts.values());
  return Math.max(...[...counts].filter(([, n]) => n >= share * max).map(([y]) => y));
}
