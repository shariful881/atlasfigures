// Small, named checks for story sentences (task 149). Each returns a plain value, so a page writes
// assertClaim(highestSince(s.remittances, L) === null, 'remittances in 2025 a record')
// and scripts/verify/_wdi.py has the same functions (same names, same rules) for the independent check.
// A Series is [year, value][] with years ascending (src/lib/econ.ts).
type Series = [number, number][];

const at = (s: Series, y: number) => s.find(([x]) => x === y)?.[1];

/** Latest earlier year whose value is >= the value in `year`; null = highest on record. */
export function highestSince(s: Series, year: number): number | null {
  const v = at(s, year);
  if (v == null) throw new Error(`no value for ${year}`);
  const prev = s.filter(([y, x]) => y < year && x >= v);
  return prev.length ? prev.at(-1)![0] : null;
}
/** Latest earlier year whose value is <= the value in `year`; null = lowest on record. */
export function lowestSince(s: Series, year: number): number | null {
  const v = at(s, year);
  if (v == null) throw new Error(`no value for ${year}`);
  const prev = s.filter(([y, x]) => y < year && x <= v);
  return prev.length ? prev.at(-1)![0] : null;
}
/** Run of consecutive yearly rises (dir 'up') or falls ('down') ending in the last year of the series.
 *  Counts only back-to-back calendar years; a gap ends the run. `years` = number of rises/falls. */
export function streak(s: Series): { dir: 'up' | 'down' | 'flat'; years: number; from: number } {
  if (s.length < 2) return { dir: 'flat', years: 0, from: s.at(-1)?.[0] ?? 0 };
  const sign = (i: number) => Math.sign(s[i][1] - s[i - 1][1]);
  const d = sign(s.length - 1);
  let i = s.length - 1;
  while (i > 0 && s[i][0] - s[i - 1][0] === 1 && sign(i) === d && d !== 0) i--;
  return { dir: d > 0 ? 'up' : d < 0 ? 'down' : 'flat', years: s.length - 1 - i, from: s[i][0] };
}
/** First year the value went above `t` and stayed above it every year after (null if it is not above now). */
export function aboveSince(s: Series, t: number): number | null {
  if (!s.length || s.at(-1)![1] <= t) return null;
  let i = s.length - 1;
  while (i > 0 && s[i - 1][1] > t) i--;
  return s[i][0];
}
/** Same, below `t`. */
export function belowSince(s: Series, t: number): number | null {
  if (!s.length || s.at(-1)![1] >= t) return null;
  let i = s.length - 1;
  while (i > 0 && s[i - 1][1] < t) i--;
  return s[i][0];
}
/** Ratio of the value in y1 to the value in y0. */
export function times(s: Series, y0: number, y1: number): number {
  const a = at(s, y0), b = at(s, y1);
  if (a == null || b == null || a === 0) throw new Error(`no ratio ${y0}->${y1}`);
  return b / a;
}
/** 1-based position of `iso` among `values` (iso → value), highest first; ties broken by iso3 like rankBy. */
export function placeAmong(values: Record<string, number>, iso: string, lowestFirst = false): number {
  const order = Object.entries(values).sort((a, b) => (lowestFirst ? a[1] - b[1] : b[1] - a[1]) || a[0].localeCompare(b[0]));
  const i = order.findIndex(([k]) => k === iso);
  if (i < 0) throw new Error(`${iso} not in list`);
  return i + 1;
}
