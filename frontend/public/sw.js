// MN-005: Service worker for market-news Next.js PWA.
// Strategy: network-first for HTML/JSON (always fresh); cache-first for icons (rarely change).
const CACHE = 'market-news-nextjs-v1';

self.addEventListener('install', () => {
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  const isIcon = url.pathname.match(/\.(png|ico)$/);

  if (isIcon) {
    // icons: cache-first (rarely change)
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(res => {
        caches.open(CACHE).then(c => c.put(e.request, res.clone()));
        return res;
      }))
    );
    return;
  }

  // HTML + JSON + Next.js routes: network-first (always get latest, offline fallback)
  e.respondWith(
    fetch(e.request)
      .then(r => {
        caches.open(CACHE).then(c => c.put(e.request, r.clone()));
        return r;
      })
      .catch(() => caches.match(e.request))
  );
});
