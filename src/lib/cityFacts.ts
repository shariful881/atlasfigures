// Small helpers for the city time pages' own sentences: every number in the prose comes from these, and the
// sentences that depend on history are guarded with assertClaim (build fails if the tz data says otherwise).
import { offsetMin, transitions, utcLabel, local } from './tz';
import { sunTimes } from './sun';
export { assertClaim } from './figures';
export const Y = 2026;
export const JAN = Date.UTC(Y, 0, 15, 12), JUL = Date.UTC(Y, 6, 15, 12);
/** Hours that city B is ahead of city A at an instant (negative = behind), e.g. 5.5. */
export const hoursAhead = (a: string, b: string, at: number) => (offsetMin(b, at) - offsetMin(a, at)) / 60;
/** "5", "5.5" → "5", "5½"; "0.5" → "half an". */
export const hrs = (h: number) => { const a = Math.abs(h); const w = Math.floor(a); const half = a - w === 0.5; return half ? (w ? `${w}½` : 'half an') : String(w); };
/** Every offset change between two years (inclusive start, exclusive end). */
export const history = (tz: string, from: number, to: number) =>
  transitions(tz, Date.UTC(from, 0, 1), Date.UTC(to, 0, 1)).map((t) => ({
    ...t, year: local(tz, t.at).y,
    date: new Date(t.at).toLocaleDateString('en-GB', { timeZone: tz, day: 'numeric', month: 'long', year: 'numeric' }),
    before: t.before, after: t.after, beforeL: utcLabel(t.before), afterL: utcLabel(t.after),
  }));
/** Daylight length in minutes on a date. */
export const dayMinutes = (y: number, m: number, d: number, lat: number, lon: number) => { const s = sunTimes(y, m, d, lat, lon); return Math.round((s.set! - s.rise!) / 60000); };
/** Year's longest and shortest daylight (minutes). */
export function dayExtremes(lat: number, lon: number, y = Y) {
  let max = 0, min = 1e9;
  for (let i = 0; i < 365; i++) { const d = new Date(Date.UTC(y, 0, 1 + i)); const L = dayMinutes(y, d.getUTCMonth() + 1, d.getUTCDate(), lat, lon); max = Math.max(max, L); min = Math.min(min, L); }
  return { max, min };
}
export const hm = (min: number) => `${Math.floor(min / 60)} hours ${min % 60} minutes`;
/** Solar noon (local clock, minutes after midnight) on a date. */
export const solarNoonMin = (tz: string, y: number, m: number, d: number, lat: number, lon: number) => { const l = local(tz, sunTimes(y, m, d, lat, lon).noon); return l.h * 60 + l.min; };
export const clock = (min: number) => `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`;
export { utcLabel, offsetMin };
import { sunRows } from './tz';
/** Sunrise/sunset clock strings on a date. */
export const sunOn = (tz: string, lat: number, lon: number, m: number, d: number, y = Y) => sunRows(tz, lat, lon, [[y, m, d]])[0];
/** Other ways to write a day length, so pages do not all share one phrase. */
export const hmS = (min: number) => `${Math.floor(min / 60)} h ${min % 60} min`;
export const hmA = (min: number) => `${Math.floor(min / 60)} hours and ${min % 60} minutes`;
