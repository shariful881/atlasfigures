// CSV behind /rankings/co2-emissions-by-country/ (its Dataset distribution). Values exactly as the Global Carbon
// Project publishes them; rank = position among UN-listed countries and areas with a value for that year.
import { energyMeta, energyOf, rankEnergy, energyYear, valueIn } from '../../lib/energy';
import { commonName } from '../../lib/names';

export function GET() {
  const y = energyYear('co2'), G = energyMeta.gcb;
  const q = (v: unknown) => (typeof v === 'string' && /[",]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v ?? '');
  const lines = rankEnergy('co2', y).map((e) => {
    const s = energyOf(e.iso3).series;
    return [e.rank, q(commonName(e.iso3)), e.iso3, y, e.value, valueIn(s.co2pc, y), valueIn(s.co2, y - 1)].map(q).join(',');
  });
  const note = [
    `# co2-emissions-by-country, ${y}. Source: ${G.name}, version ${G.version} (${G.url}), file ${G.file}. Licence: ${G.licence}.`,
    '# Territorial fossil CO2 (fossil fuels, cement, flaring), million tonnes; per person in tonnes. Values exactly as published; only countries and areas with a value for this year are ranked.',
  ];
  const head = ['rank', 'country_or_area', 'iso3', 'year', 'co2_million_tonnes', 'co2_tonnes_per_person', 'co2_previous_year_million_tonnes'].join(',');
  return new Response([...note, head, ...lines].join('\n') + '\n', { headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'inline; filename="co2-emissions-by-country.csv"' } });
}
