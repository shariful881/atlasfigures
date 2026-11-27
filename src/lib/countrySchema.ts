// Structured data shared by every country page: Article + Dataset (real CSV) + FAQPage.
// Only the code is shared; every text passed in (headline, description, FAQ) is the page's own.
import { abs, ORG_ID, WEBSITE_ID, PUBLISHER } from '../site';

const UN_DESA = { '@type': 'Organization', name: 'United Nations, Department of Economic and Social Affairs, Population Division' };

export interface SchemaInput {
  page: string;                 // e.g. '/country/india/population/'
  slug: string;
  name: string;                 // common English name
  wikipedia: string;
  headline: string;
  description: string;
  datasetName: string;
  datasetDescription: string;
  temporalCoverage: string;     // '1950/2100'
  published: string;            // YYYY-MM-DD
  updated: string;
  tz?: string;                  // '+06:00'
  wppUrl: string;
  wupUrl: string;
  extraCitations?: { name: string; url: string; publisher: string }[];
  faq: { q: string; a: string }[];
}

export function countrySchema(s: SchemaInput) {
  const iso = (d: string) => `${d}T12:00:00${s.tz ?? '+06:00'}`;
  return [
    {
      '@type': 'Article',
      '@id': abs(`${s.page}#article`),
      headline: s.headline,
      description: s.description,
      datePublished: iso(s.published),
      dateModified: iso(s.updated),
      author: { '@type': 'Organization', name: PUBLISHER, url: abs('/about/') },
      publisher: { '@id': ORG_ID },
      isPartOf: { '@id': WEBSITE_ID },
      mainEntityOfPage: abs(s.page),
      image: abs('/icon-512.png'),
      inLanguage: 'en',
      about: { '@type': 'Country', name: s.name, sameAs: s.wikipedia },
      citation: [
        { '@type': 'CreativeWork', name: 'World Population Prospects 2024', url: s.wppUrl, publisher: UN_DESA },
        { '@type': 'CreativeWork', name: 'World Urbanization Prospects 2025', url: s.wupUrl, publisher: UN_DESA },
        ...(s.extraCitations ?? []).map((c) => ({ '@type': 'CreativeWork', name: c.name, url: c.url, publisher: { '@type': 'Organization', name: c.publisher } })),
      ],
    },
    {
      '@type': 'Dataset',
      '@id': abs(`${s.page}#dataset`),
      name: s.datasetName,
      description: s.datasetDescription,
      url: abs(s.page),
      creator: { '@id': ORG_ID },
      isBasedOn: [s.wppUrl, s.wupUrl],
      temporalCoverage: s.temporalCoverage,
      spatialCoverage: { '@type': 'Place', name: s.name },
      variableMeasured: ['Population', 'Population density (people per km²)', 'Total fertility rate', 'Median age', 'Urban population (%, national definition)', 'Net migrants', 'World population rank'],
      dateModified: iso(s.updated),
      license: 'https://creativecommons.org/licenses/by/3.0/igo/',
      distribution: [{ '@type': 'DataDownload', encodingFormat: 'text/csv', contentUrl: abs(`/data/${s.slug}-population.csv`) }],
    },
    {
      '@type': 'FAQPage',
      '@id': abs(`${s.page}#faq`),
      mainEntity: s.faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })),
    },
  ];
}
