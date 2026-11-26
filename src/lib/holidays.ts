// Holiday-list helpers (task 28). Dates come from the editorial file src/data/holidays/<slug>.json (copied from the
// government notification, see `source` and `verification` there); weekdays, weekend overlaps, long breaks and the
// Islamic (Umm al-Qura) calendar dates are computed here, never typed.
export type Holiday = { date: string; name: string; type: 'general' | 'executive'; lunar: boolean; note?: string };
export const WEEKEND_BD = [5, 6]; // Friday, Saturday (getUTCDay)
const day = (iso: string) => new Date(`${iso}T00:00:00Z`);
export const weekday = (iso: string) => day(iso).toLocaleDateString('en-GB', { weekday: 'long', timeZone: 'UTC' });
export const dShort = (iso: string) => day(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', timeZone: 'UTC' });
export const isWeekend = (iso: string, wk = WEEKEND_BD) => wk.includes(day(iso).getUTCDay());
const addDays = (iso: string, n: number) => new Date(day(iso).getTime() + n * 86400000).toISOString().slice(0, 10);

/** Runs of 3 or more consecutive days off (holidays plus the weekly weekend). */
export function breaks(list: Holiday[], year: number, wk = WEEKEND_BD) {
  const off = new Set(list.map((h) => h.date));
  const out: { from: string; to: string; days: number; names: string[] }[] = [];
  let d = `${year}-01-01`;
  while (d.startsWith(String(year))) {
    if (off.has(d) || isWeekend(d, wk)) {
      let e = d; const names = new Set<string>();
      while (off.has(e) || isWeekend(e, wk)) { list.filter((h) => h.date === e).forEach((h) => names.add(h.name.replace(/ holiday \((before|after) Eid\)/, ''))); e = addDays(e, 1); }
      const n = Math.round((day(e).getTime() - day(d).getTime()) / 86400000);
      if (n >= 3 && names.size) out.push({ from: d, to: addDays(e, -1), days: n, names: [...names] });
      d = e;
    } else d = addDays(d, 1);
  }
  return out;
}
/** Gregorian date of a day in the Umm al-Qura Islamic calendar (built into the JavaScript runtime). */
export function ummAlQura(hYear: number, hMonth: number, hDay: number, nearYear: number) {
  const f = new Intl.DateTimeFormat('en-u-ca-islamic-umalqura', { year: 'numeric', month: 'numeric', day: 'numeric', timeZone: 'UTC' });
  for (let t = Date.UTC(nearYear - 1, 0, 1); t < Date.UTC(nearYear + 1, 11, 31); t += 86400000) {
    const [m, d, y] = f.format(t).replace(/\s*AH$/, '').split('/').map(Number);
    if (y === hYear && m === hMonth && d === hDay) return new Date(t).toISOString().slice(0, 10);
  }
  return null;
}
