// Site catalog for the home page and the Rankings hub: every published ranking with its topic, the year it uses,
// how many places it ranks, the world figure and the place in first position. Every figure is computed with the
// SAME functions the ranking page itself uses (rankBy / rankEnergy / byPopulation …), so the hub can never show a
// different number or a different leader from the page it links to. Nothing here is typed by hand.
import { aggregate, valueIn as wbIn, rankBy, rankingYear, coverageYear, usd, usdWhole, type IndicatorKey } from './econ';
import { worldEnergy, valueIn as enIn, rankEnergy, energyYear, tonnes } from './energy';
import { byPopulation, byDensity } from './popRankings';
import { worldData, byYear, CURRENT_YEAR, int, pct, people } from './figures';
import { commonName, iso2 } from './names';

export type Topic = 'population' | 'economy' | 'energy' | 'telecom' | 'health';
export const TOPICS: { key: Topic; label: string; text: string }[] = [
  { key: 'population', label: 'Population', text: 'How many people live in each place, and how closely packed they are.' },
  { key: 'economy', label: 'Economy', text: 'Output, income, prices, jobs and money sent home from abroad.' },
  { key: 'energy', label: 'Energy and climate', text: 'Fossil CO₂ and how much electricity comes from renewables.' },
  { key: 'telecom', label: 'Internet and mobile', text: 'Who is online and how many phone and broadband lines there are.' },
  { key: 'health', label: 'Health', text: 'Survival of mothers and young children.' },
];

export type RankingCard = {
  slug: string; href: string; topic: Topic; title: string; blurb: string; source: string;
  year: number; count: number; unit: string;
  world: { label: string; value: string } | null;
  leader: { iso3: string; name: string; flag: string | null; value: string; label: string } | null;
};

const lead = (iso3: string, value: string, label = 'Ranked first') => ({ iso3, name: commonName(iso3), flag: iso2(iso3), value, label });
const WLD = () => aggregate('WLD').series;

function wb(slug: string, topic: Topic, title: string, blurb: string, key: IndicatorKey, fmt: (v: number) => string,
  opts: { coverage?: boolean; worldLabel?: string; leaderLabel?: string; unit: string; source?: string }): RankingCard {
  const year = opts.coverage ? coverageYear(key) : rankingYear(key);
  const ranked = rankBy(key, year);
  const w = wbIn(WLD()[key], year);
  return {
    slug, href: `/rankings/${slug}/`, topic, title, blurb, year, count: ranked.length, unit: opts.unit,
    source: opts.source ?? 'World Bank WDI',
    world: w == null ? null : { label: opts.worldLabel ?? 'World', value: fmt(w) },
    leader: lead(ranked[0].iso3, fmt(ranked[0].value), opts.leaderLabel),
  };
}

export function rankingCards(): RankingCard[] {
  const wPop = byYear(worldData.years)[CURRENT_YEAR];
  const pop = byPopulation(), dens = byDensity();
  const co2Y = energyYear('co2'), co2 = rankEnergy('co2', co2Y);
  const renY = energyYear('renShare'), ren = rankEnergy('renShare', renY);
  const perKm = (v: number) => `${int(v)} per km²`;
  const cards: RankingCard[] = [
    {
      slug: 'population-by-country', href: '/rankings/population-by-country/', topic: 'population',
      title: 'Population by country', blurb: 'Every country and area in the UN data, largest first, with growth and the 2050 outlook.',
      source: 'UN WPP 2024', year: CURRENT_YEAR, count: pop.length, unit: 'people',
      world: { label: 'World', value: people(wPop.population) }, leader: lead(pop[0].iso3, people(pop[0].now.population), 'Most people'),
    },
    {
      slug: 'population-density-by-country', href: '/rankings/population-density-by-country/', topic: 'population',
      title: 'Population density by country', blurb: 'People per square kilometre of land, from crowded city-states to empty ice sheets.',
      source: 'UN WPP 2024', year: CURRENT_YEAR, count: dens.length, unit: 'people per km²',
      world: { label: 'World', value: perKm(wPop.densityPerKm2) }, leader: lead(dens[0].iso3, perKm(dens[0].now.densityPerKm2), 'Most crowded'),
    },
    wb('gdp-by-country', 'economy', 'GDP by country', 'The size of every economy in current US dollars.', 'gdp', usd, { unit: 'US$', leaderLabel: 'Largest' }),
    wb('gdp-per-capita-by-country', 'economy', 'GDP per capita by country', 'Output per person, from the richest economies to the poorest.', 'gdpPerCapita', usdWhole, { unit: 'US$ per person', worldLabel: 'World average', leaderLabel: 'Highest' }),
    wb('inflation-rate-by-country', 'economy', 'Inflation rate by country', 'How fast consumer prices rose over the year, and where they fell.', 'inflationPct', pct, { unit: '% a year', leaderLabel: 'Highest' }),
    wb('unemployment-rate-by-country', 'economy', 'Unemployment rate by country', 'Share of the labour force without work, ILO modelled estimates.', 'unemploymentPct', pct, { unit: '% of labour force', leaderLabel: 'Highest', source: 'ILO via World Bank' }),
    wb('remittances-by-country', 'economy', 'Remittances by country', 'Money sent home by people working abroad, in dollars and as a share of GDP.', 'remittances', usd, { unit: 'US$ received', worldLabel: 'World total', leaderLabel: 'Most received' }),
    {
      slug: 'co2-emissions-by-country', href: '/rankings/co2-emissions-by-country/', topic: 'energy',
      title: 'CO₂ emissions by country', blurb: 'Fossil CO₂ from each country, in total and per person.',
      source: 'Global Carbon Project', year: co2Y, count: co2.length, unit: 'tonnes of CO₂',
      world: { label: 'World', value: tonnes(enIn(worldEnergy.series.co2, co2Y)!) }, leader: lead(co2[0].iso3, tonnes(co2[0].value), 'Largest emitter'),
    },
    {
      slug: 'renewable-electricity-by-country', href: '/rankings/renewable-electricity-by-country/', topic: 'energy',
      title: 'Renewable electricity by country', blurb: 'Share of power from hydro, wind, solar and other renewables.',
      source: 'Ember', year: renY, count: ren.length, unit: '% of electricity',
      // Several countries tie at (almost) 100%, so naming one "first" would mislead: show the world share only.
      world: { label: 'World', value: pct(enIn(worldEnergy.series.renShare, renY)!) }, leader: null,
    },
    wb('internet-users-by-country', 'telecom', 'Internet users by country', 'Share of people who used the internet in the year.', 'internetPct', pct, { coverage: true, unit: '% of people', leaderLabel: 'Highest', source: 'ITU via World Bank' }),
    wb('mobile-subscriptions-by-country', 'telecom', 'Mobile subscriptions by country', 'Mobile and fixed broadband subscriptions for every 100 people.', 'mobilePer100', (v) => `${v.toFixed(1)} per 100`, { coverage: true, unit: 'per 100 people', leaderLabel: 'Highest', source: 'ITU via World Bank' }),
    wb('child-mortality-by-country', 'health', 'Child mortality by country', 'Children who die before age five, per 1,000 live births.', 'under5Mortality', (v) => `${v.toFixed(1)} per 1,000`, { unit: 'per 1,000 births', leaderLabel: 'Highest', source: 'UN IGME via World Bank' }),
    wb('maternal-mortality-by-country', 'health', 'Maternal mortality by country', 'Women who die from pregnancy or childbirth, per 100,000 live births.', 'maternalMortality', (v) => `${int(v)} per 100,000`, { unit: 'per 100,000 births', leaderLabel: 'Highest', source: 'UN MMEIG via World Bank' }),
  ];
  return cards;
}

/** Population pages grouped by the UN's continent (Americas = Latin America and the Caribbean + Northern America). */
export const CONTINENT: Record<string, string> = { Africa: 'Africa', Asia: 'Asia', Europe: 'Europe', Oceania: 'Oceania', 'Latin America and the Caribbean': 'Americas', 'Northern America': 'Americas' };
