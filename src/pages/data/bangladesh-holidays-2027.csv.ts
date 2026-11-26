// CSV of the Bangladesh 2027 holiday list (same file as the page: src/data/holidays/bangladesh-2027.json).
import data from '../../data/holidays/bangladesh-2027.json';
import { weekday } from '../../lib/holidays';
export function GET() {
  const q = (s: string) => `"${s.replace(/"/g, '""')}"`;
  const rows = [...data.holidays].sort((a, b) => a.date.localeCompare(b.date)).map((h: any) => [h.date, weekday(h.date), q(h.name), h.type, h.lunar ? 'yes' : 'no', q(h.note ?? '')].join(','));
  const body = ['date,weekday,holiday,type,depends_on_moon,note', ...rows].join('\n') + '\n';
  return new Response(body, { headers: { 'Content-Type': 'text/csv; charset=utf-8' } });
}
