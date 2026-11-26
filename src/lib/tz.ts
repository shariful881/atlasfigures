// Time-zone facts from the IANA tz database as built into the JavaScript runtime (Node's ICU at build time — tz
// 2026e here — and the visitor's browser for the live clock). Nothing is typed by hand: offsets, daylight-saving
// dates and zone names on the time pages all come from these functions.
import { sunTimes } from './sun';

/** UTC offset in minutes for a time zone at an instant. */
const fmts = new Map<string, Intl.DateTimeFormat>();
export function offsetMin(tz: string, at: number | Date): number {
  let f = fmts.get(tz);
  if (!f) { f = new Intl.DateTimeFormat('en-US', { timeZone: tz, timeZoneName: 'longOffset' }); fmts.set(tz, f); }
  const s = f.formatToParts(new Date(at)).find((p) => p.type === 'timeZoneName')!.value;
  const m = s.match(/GMT([+-])(\d{2}):?(\d{2})?/);
  if (!m) return 0; // "GMT"
  return (m[1] === '-' ? -1 : 1) * (Number(m[2]) * 60 + Number(m[3] ?? 0));
}
/** "UTC+5:30", "UTC−5", "UTC+0" (true minus sign). */
export function utcLabel(min: number) {
  const sign = min < 0 ? '−' : '+';
  const a = Math.abs(min), h = Math.floor(a / 60), mm = a % 60;
  return `UTC${sign}${h}${mm ? `:${String(mm).padStart(2, '0')}` : ''}`;
}
/** Long zone name, e.g. "British Summer Time", for an instant. */
export function zoneName(tz: string, at: number | Date, locale = 'en-GB') {
  return new Intl.DateTimeFormat(locale, { timeZone: tz, timeZoneName: 'long' }).formatToParts(new Date(at)).find((p) => p.type === 'timeZoneName')!.value;
}
/** Every offset change in [from, to): instant (UTC ms, exact to the minute) and offsets before/after. */
export function transitions(tz: string, from: number, to: number) {
  const out: { at: number; before: number; after: number }[] = [];
  const D = 6 * 3600000; // offsets never change twice within six hours
  const cache = new Map<number, number>();
  const off = (t: number) => { let v = cache.get(t); if (v === undefined) { v = offsetMin(tz, t); cache.set(t, v); } return v; };
  let prev = off(from);
  for (let t = from + D; t < to + D; t += D) {
    const tt = Math.min(t, to);
    const cur = off(tt);
    if (cur !== prev) {
      let lo = tt - D, hi = tt; // binary search to the minute
      while (hi - lo > 60000) { const mid = lo + Math.floor((hi - lo) / 120000) * 60000; if (off(mid) === prev) lo = mid; else hi = mid; }
      out.push({ at: hi, before: prev, after: cur });
      prev = cur;
    }
    if (tt === to) break;
  }
  return out;
}
/** Year boundaries in UTC. */
export const yearSpan = (y: number) => [Date.UTC(y, 0, 1), Date.UTC(y + 1, 0, 1)] as const;
/** Offsets seen during a year (one value = no daylight saving). */
export const offsetsIn = (tz: string, y: number) => {
  const [a, b] = yearSpan(y);
  return [...new Set([offsetMin(tz, a), ...transitions(tz, a, b).map((t) => t.after)])].sort((x, z) => x - z);
};
/** Local wall-clock parts of an instant in a zone. */
const lfmts = new Map<string, Intl.DateTimeFormat>();
export function local(tz: string, at: number) {
  let f = lfmts.get(tz);
  if (!f) { f = new Intl.DateTimeFormat('en-GB', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }); lfmts.set(tz, f); }
  const p = Object.fromEntries(f.formatToParts(new Date(at)).map((x) => [x.type, x.value]));
  return { y: +p.year, m: +p.month, d: +p.day, h: +p.hour, min: +p.minute };
}
export const hhmm = (tz: string, at: number) => { const l = local(tz, at); return `${String(l.h).padStart(2, '0')}:${String(l.min).padStart(2, '0')}`; };
export const dateLong = (tz: string, at: number) => new Date(at).toLocaleDateString('en-GB', { timeZone: tz, day: 'numeric', month: 'long', year: 'numeric' });
export const weekdayDate = (tz: string, at: number) => new Date(at).toLocaleDateString('en-GB', { timeZone: tz, weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });

/** Sun table: one row per date, times in the city's own clock time. */
export function sunRows(tz: string, lat: number, lon: number, dates: [number, number, number][]) {
  return dates.map(([y, m, d]) => {
    const s = sunTimes(y, m, d, lat, lon);
    const len = s.rise && s.set ? Math.round((s.set - s.rise) / 60000) : null;
    return { y, m, d, rise: s.rise && hhmm(tz, s.rise), set: s.set && hhmm(tz, s.set), noon: hhmm(tz, s.noon), lenMin: len };
  });
}
export const dayLen = (min: number) => `${Math.floor(min / 60)} h ${String(min % 60).padStart(2, '0')} min`;
