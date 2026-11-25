// Service worker: network-first for pages (fresh numbers), falling back to the
// cached copy when offline, so pages you've opened still work like an app.
export function GET() {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  const js = `
const CACHE = 'af-v1';
self.addEventListener('install', (e) => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then((c) => c.addAll(['${base}/']))); });
self.addEventListener('activate', (e) => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    fetch(req).then((res) => { const copy = res.clone(); caches.open(CACHE).then((c) => c.put(req, copy)); return res; })
      .catch(() => caches.match(req).then((r) => r || caches.match('${base}/')))
  );
});`;
  return new Response(js, { headers: { 'Content-Type': 'application/javascript' } });
}
