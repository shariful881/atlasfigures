// "Remind me" calendar file for the Eid-ul-Fitr countdown: one all-day event on the date in the government list.
import data from '../../data/holidays/bangladesh-2027.json';
export function GET() {
  const d = data.holidays.find((h: any) => h.name === 'Eid-ul-Fitr')!.date;
  const next = new Date(new Date(`${d}T00:00:00Z`).getTime() + 86400000).toISOString().slice(0, 10).replace(/-/g, '');
  const body = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AtlasFigures//Eid-ul-Fitr 2027//EN', 'BEGIN:VEVENT', `UID:eid-ul-fitr-2027@atlasfigures.com`, 'DTSTAMP:20261126T000000Z',
    `DTSTART;VALUE=DATE:${d.replace(/-/g, '')}`, `DTEND;VALUE=DATE:${next}`, 'SUMMARY:Eid-ul-Fitr (Bangladesh\\, subject to moon sighting)',
    'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:Eid-ul-Fitr tomorrow', 'TRIGGER:-P1D', 'END:VALARM', 'END:VEVENT', 'END:VCALENDAR'].join('\r\n') + '\r\n';
  return new Response(body, { headers: { 'Content-Type': 'text/calendar; charset=utf-8' } });
}
