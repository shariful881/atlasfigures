// Two-city time facts (task 27). Everything is derived from the IANA tz data in the runtime (src/lib/tz.ts).
import { offsetMin, transitions, local, utcLabel } from './tz';

export const Y = 2026;
export const JAN = Date.UTC(Y, 0, 15, 12), JUL = Date.UTC(Y, 6, 15, 12);

/** Minutes that B is ahead of A at an instant (negative: B behind). */
export const gapMin = (a: string, b: string, at: number) => offsetMin(b, at) - offsetMin(a, at);
/** "5 h", "5 h 30 min", "30 min". */
export function gapText(min: number) {
  const m = Math.abs(min), h = Math.floor(m / 60), r = m % 60;
  return [h ? `${h} h` : '', r ? `${r} min` : ''].filter(Boolean).join(' ') || '0 h';
}
/** "+5:30" style badge. */
export const gapBadge = (min: number) => `${min < 0 ? '−' : '+'}${Math.floor(Math.abs(min) / 60)}${Math.abs(min) % 60 ? ':' + String(Math.abs(min) % 60).padStart(2, '0') : ''}`;

/** Periods of the year with the same gap (B minus A), from 1 January to 31 December of year y. */
export function gapPeriods(a: string, b: string, y = Y) {
  const s = Date.UTC(y, 0, 1), e = Date.UTC(y + 1, 0, 1);
  const cuts = [...transitions(a, s, e), ...transitions(b, s, e)].map((t) => t.at).sort((x, z) => x - z);
  const points = [s, ...cuts, e];
  const out: { from: number; to: number; gap: number }[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    const g = gapMin(a, b, points[i] + 1000);
    if (out.length && out[out.length - 1].gap === g) out[out.length - 1].to = points[i + 1];
    else out.push({ from: points[i], to: points[i + 1], gap: g });
  }
  return out;
}
/** Same as gapPeriods, but spells shorter than a day (when both cities change clocks on the same night, a few hours
 *  apart) are folded into the neighbouring period; `blips` lists them so the page can say so. */
export function gapSeasons(a: string, b: string, y = Y) {
  const raw = gapPeriods(a, b, y);
  const blips = raw.filter((x) => x.to - x.from < 86400000);
  const out: typeof raw = [];
  for (const x of raw.filter((r) => r.to - r.from >= 86400000)) {
    if (out.length && out[out.length - 1].gap === x.gap) out[out.length - 1].to = x.to;
    else { if (out.length) out[out.length - 1].to = x.from; out.push({ ...x }); }
  }
  return { periods: out, blips };
}

/** Local wall time (minutes after midnight) in zone `to` for a wall time in zone `from` on a reference instant's date. */
export function convertWall(from: string, to: string, ref: number, minutes: number) {
  const l = local(from, ref);
  const guess = Date.UTC(l.y, l.m - 1, l.d) + minutes * 60000 - offsetMin(from, ref) * 60000;
  const t = local(to, guess), f = local(from, guess);
  const dayShift = Date.UTC(t.y, t.m - 1, t.d) - Date.UTC(f.y, f.m - 1, f.d);
  return { min: t.h * 60 + t.min, day: Math.round(dayShift / 86400000) };
}
export const hhmm = (m: number) => `${String(Math.floor(m / 60)).padStart(2, '0')}:${String(m % 60).padStart(2, '0')}`;

/** Overlap of 09:00–17:00 office hours in both cities on a reference date, as A's local times. */
export function officeOverlap(a: string, b: string, ref: number, start = 9 * 60, end = 17 * 60) {
  const g = gapMin(a, b, ref); // B = A + g
  const lo = Math.max(start, start - g), hi = Math.min(end, end - g);
  return hi > lo ? { from: lo, to: hi, len: hi - lo } : null;
}
export { utcLabel, offsetMin };
