// Columns of the yearly tables and CSVs on country topic pages (task 160). Each column is one World Bank WDI
// series; the table shows it rounded to `digits`, the CSV holds the value exactly as published.
import type { IndicatorKey } from './econ';
export type TopicCol = { key: string; wdi: IndicatorKey; label: string; unit?: string; digits: number; csv: string };

export const HEALTH_COLS: TopicCol[] = [
  { key: 'u5', wdi: 'under5Mortality', label: 'Deaths before age 5', unit: 'per 1,000 births', digits: 1, csv: 'under5_deaths_per_1000_live_births' },
  { key: 'infant', wdi: 'infantMortality', label: 'Infant deaths', unit: 'per 1,000 births', digits: 1, csv: 'infant_deaths_per_1000_live_births' },
  { key: 'neonatal', wdi: 'neonatalMortality', label: 'Newborn deaths', unit: 'per 1,000 births', digits: 1, csv: 'newborn_deaths_first_28_days_per_1000_live_births' },
  { key: 'maternal', wdi: 'maternalMortality', label: 'Maternal deaths', unit: 'per 100,000 births', digits: 0, csv: 'maternal_deaths_per_100000_live_births' },
  { key: 'measles', wdi: 'measlesVaccPct', label: 'Measles vaccine', unit: '% of children', digits: 0, csv: 'measles_vaccination_pct_children_12_23_months' },
  { key: 'healthGdp', wdi: 'healthSpendPctGdp', label: 'Health spending', unit: '% of GDP', digits: 1, csv: 'current_health_expenditure_pct_gdp' },
  { key: 'oop', wdi: 'outOfPocketPct', label: 'Out of pocket', unit: '% of spending', digits: 1, csv: 'out_of_pocket_pct_current_health_expenditure' },
];
// Extra series in the health CSV only
export const HEALTH_CSV_EXTRA: TopicCol[] = [
  { key: 'dpt', wdi: 'dptVaccPct', label: 'DPT vaccine', digits: 0, csv: 'dpt_vaccination_pct_children_12_23_months' },
  { key: 'doctors', wdi: 'doctorsPer1000', label: 'Doctors', digits: 2, csv: 'doctors_per_1000_people' },
  { key: 'nurses', wdi: 'nursesPer1000', label: 'Nurses and midwives', digits: 2, csv: 'nurses_and_midwives_per_1000_people' },
  { key: 'beds', wdi: 'hospitalBedsPer1000', label: 'Hospital beds', digits: 1, csv: 'hospital_beds_per_1000_people' },
  { key: 'healthPc', wdi: 'healthSpendPerCapita', label: 'Health spending per person', digits: 0, csv: 'current_health_expenditure_per_person_current_usd' },
  { key: 'stunting', wdi: 'stuntingPct', label: 'Stunting', digits: 1, csv: 'stunting_pct_children_under_5' },
  { key: 'undernour', wdi: 'undernourishedPct', label: 'Undernourishment', digits: 1, csv: 'undernourishment_pct_population' },
  { key: 'diabetes', wdi: 'diabetesPct', label: 'Diabetes', digits: 1, csv: 'diabetes_pct_ages_20_79' },
  { key: 'tb', wdi: 'tbIncidence', label: 'Tuberculosis', digits: 0, csv: 'tuberculosis_new_cases_per_100000' },
  { key: 'malaria', wdi: 'malariaIncidence', label: 'Malaria', digits: 1, csv: 'malaria_new_cases_per_1000_at_risk' },
  { key: 'tobacco', wdi: 'tobaccoPct', label: 'Tobacco use', digits: 1, csv: 'tobacco_use_pct_adults' },
  { key: 'road', wdi: 'roadDeathsPer100k', label: 'Road deaths', digits: 1, csv: 'road_traffic_deaths_per_100000' },
];
