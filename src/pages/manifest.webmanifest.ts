// PWA manifest: lets phones install AtlasFigures to the home screen and open it full-screen like an app.
export function GET() {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const manifest = {
    name: 'AtlasFigures',
    short_name: 'AtlasFigures',
    description: 'World population, time, economy and country rankings.',
    start_url: `${base}/`,
    scope: `${base}/`,
    display: 'standalone',
    background_color: '#eef5f7',
    theme_color: '#f7f9f9',
    icons: [
      { src: `${base}/icon-192.png`, sizes: '192x192', type: 'image/png' },
      { src: `${base}/icon-512.png`, sizes: '512x512', type: 'image/png' },
      { src: `${base}/icon-512.png`, sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
  };
  return new Response(JSON.stringify(manifest), { headers: { 'Content-Type': 'application/manifest+json' } });
}
