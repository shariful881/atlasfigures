// Calendar file (iCalendar, all-day events) of the Bangladesh 2027 holiday list, for "Add to calendar".
import data from '../../data/holidays/bangladesh-2027.json';
export function GET() {
  const next = (d: string) => new Date(new Date(`${d}T00:00:00Z`).getTime() + 86400000).toISOString().slice(0, 10).replace(/-/g, '');
  const esc = (s: string) => s.replace(/[\;,]/g, (c) => `\\${c}`);
  const ev = [...data.holidays].sort((a, b) => a.date.localeCompare(b.date)).map((h: any, i: number) => [
    'BEGIN:VEVENT', `UID:bd-2027-${h.date}-${i}@atlasfigures.com`, 'DTSTAMP:20261126T000000Z',
    `DTSTART;VALUE=DATE:${h.date.replace(/-/g, '')}`, `DTEND;VALUE=DATE:${next(h.date)}`,
    `SUMMARY:${esc(h.name)}${h.lunar ? ' (subject to moon sighting)' : ''}`,
    `DESCRIPTION:${esc(`Bangladesh public holiday (${h.type === 'general' ? 'general' : 'executive order'}). Source: Ministry of Public Administration list for 2027.`)}`,
    'TRANSP:TRANSPARENT', 'END:VEVENT'].join('\r\n'));
  const body = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AtlasFigures//Bangladesh holidays 2027//EN', 'CALSCALE:GREGORIAN', 'X-WR-CALNAME:Bangladesh public holidays 2027', ...ev, 'END:VCALENDAR'].join('\r\n') + '\r\n';
  return new Response(body, { headers: { 'Content-Type': 'text/calendar; charset=utf-8' } });
}
