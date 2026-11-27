// Country profiles (task 158) for the country hub and topic pages (task 160).
// Every value comes from src/data/profiles/<ISO3>.json, which build-profiles makes from the generated data
// (UN WPP, World Bank WDI, Global Carbon Project/Ember, country facts) and check-profiles compares with it.
// Pages never type a figure by hand: they show `text` exactly as the profile holds it.
import list from '../data/country-list.json';

export type ProfileStat = {
  id?: string; label: string; status: 'live' | 'no-data' | 'planned' | 'to-check';
  value?: number | string; text?: string; unit?: string | null; year?: number | null; projection?: boolean;
  rank?: number; of?: number; rankBy?: 'high' | 'low'; source?: string; phase?: string;
};
export type ProfileSection = { id: string; label: string; stats: ProfileStat[] };
export type Profile = { iso3: string; iso2: string; slug: string; name: string; unName: string; year: number; sections: ProfileSection[] };

const files = import.meta.glob<Profile>('../data/profiles/*.json', { eager: true, import: 'default' });
export function profile(iso3: string): Profile {
  const p = files[`../data/profiles/${iso3}.json`];
  if (!p) throw new Error(`No profile for ${iso3}`);
  return p;
}
export const countryBySlug = (slug: string) => (list as any).countries.find((c: any) => c.slug === slug);

/** One live statistic by section and id (throws if it is not live, so a page cannot show a missing figure). */
export function stat(p: Profile, section: string, id: string): ProfileStat & { text: string } {
  const s = p.sections.find((x) => x.id === section)?.stats.find((x) => x.id === id);
  if (!s || s.status !== 'live' || s.text == null) throw new Error(`${p.iso3}: ${section}.${id} is not a live statistic`);
  return s as ProfileStat & { text: string };
}

// Facts that rest on Wikidata alone are shown on a page only after a hand check (listed in the page's JSON).
export const SINGLE_SOURCE_FACTS = new Set(['landlocked', 'highest', 'driving', 'plugs', 'emergency']);

/** Live statistics of a section for display; single-source facts only when `checkedFacts` names them. */
export function liveStats(p: Profile, section: string, checkedFacts: string[] = []) {
  const sec = p.sections.find((x) => x.id === section);
  if (!sec) throw new Error(`no section ${section}`);
  return sec.stats.filter((s) => s.status === 'live' && (section !== 'facts' || !SINGLE_SOURCE_FACTS.has(s.id!) || checkedFacts.includes(s.id!))) as (ProfileStat & { text: string })[];
}

/** "37th highest of 211" / "139th lowest of 196" */
export const ordinal = (n: number) => {
  const s = ['th', 'st', 'nd', 'rd'], v = n % 100;
  return `${n}${s[(v - 20) % 10] || s[v] || s[0]}`;
};
/** Place counted from the highest value (1 = highest in the world) / from the lowest (1 = lowest), whatever rankBy is. */
export const fromTop = (s: ProfileStat) => (s.rankBy === 'low' ? s.of! - s.rank! + 1 : s.rank!);
export const fromBottom = (s: ProfileStat) => s.of! - fromTop(s) + 1;
export const rankText = (s: ProfileStat) => (s.rank ? `${ordinal(s.rank)} ${s.rankBy === 'low' ? 'lowest' : 'highest'} of ${s.of}` : '');

// Ranking pages that exist for a profile statistic (section.id → /rankings/<slug>/)
export const RANKING_OF: Record<string, string> = {
  'population.population': 'population-by-country', 'population.density': 'population-density-by-country',
  'population.migrantStock': 'immigrant-population-by-country', 'population.migrantPct': 'immigrant-percentage-by-country',
  'facts.landArea': 'land-area-by-country',
  'economy.gdp': 'gdp-by-country', 'economy.gdpPc': 'gdp-per-capita-by-country', 'economy.inflation': 'inflation-rate-by-country',
  'trade.exports': 'exports-by-country', 'trade.imports': 'imports-by-country', 'trade.remit': 'remittances-by-country',
  'jobs.unemp': 'unemployment-rate-by-country', 'jobs.lfpF': 'female-labor-force-participation-by-country', 'jobs.empAgri': 'employment-in-agriculture-by-country',
  'health.u5': 'child-mortality-by-country', 'health.maternal': 'maternal-mortality-by-country',
  'education.literacy': 'literacy-rate-by-country', 'education.eduSpend': 'education-spending-by-country',
  'internet.internet': 'internet-users-by-country', 'internet.mobileSubs': 'mobile-subscriptions-by-country',
  'energy.renShare': 'renewable-electricity-by-country',
  'environment.co2': 'co2-emissions-by-country', 'environment.forestArea': 'forest-area-by-country',
};

// Topic pages a country can have (file src/pages/country/<slug>/<topic>.astro) and the profile section each covers.
export const TOPICS: { topic: string; section: string; name: string }[] = [
  { topic: 'population', section: 'population', name: 'Population' },
  { topic: 'economy', section: 'economy', name: 'Economy' },
  { topic: 'health', section: 'health', name: 'Health' },
  { topic: 'education', section: 'education', name: 'Education' },
  { topic: 'internet', section: 'internet', name: 'Internet and mobile' },
];

/** Short source name for a row ("World Bank (SH.DYN.MORT)" → "World Bank"). */
export const sourceShort = (src = '') => src.startsWith('UN WPP / World Bank') ? 'UN / World Bank' : src.startsWith('IANA') ? 'IANA tz' : src.startsWith('World Bank') ? 'World Bank' : src.startsWith('UN World Population') ? 'UN WPP 2024' : src.startsWith('UN World Urbanization') ? 'UN WUP 2025' : src.split(/[;(]/)[0].trim();
