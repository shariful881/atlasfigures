// CSV behind /rankings/renewable-electricity-by-country/ (its Dataset distribution). Values exactly as Ember
// publishes them (shares can round slightly above 100); rank = position among UN-listed countries and areas with a value.
import { energyMeta, energyOf, rankEnergy, energyYear, valueIn } from '../../lib/energy';
import { commonName } from '../../lib/names';

export function GET() {
  const y = energyYear('renShare'), E = energyMeta.ember;
  const q = (v: unknown) => (typeof v === 'string' && /[",]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v ?? '');
  const lines = rankEnergy('renShare', y).map((e) => {
    const s = energyOf(e.iso3).series;
    return [e.rank, q(commonName(e.iso3)), e.iso3, y, e.value, valueIn(s.wsShare, y), valueIn(s.ren, y), valueIn(s.gen, y)].map(q).join(',');
  });
  const note = [
    `# renewable-electricity-by-country, ${y}. Source: ${E.name} (${E.url}), downloaded ${energyMeta.downloaded}. Licence: ${E.licence}.`,
    '# Shares of electricity generation (%), generation in TWh. Values exactly as published; only countries and areas with a value for this year are ranked.',
  ];
  const head = ['rank', 'country_or_area', 'iso3', 'year', 'renewables_share_of_generation_pct', 'wind_and_solar_share_of_generation_pct', 'renewable_generation_twh', 'total_generation_twh'].join(',');
  return new Response([...note, head, ...lines].join('\n') + '\n', { headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': 'inline; filename="renewable-electricity-by-country.csv"' } });
}
