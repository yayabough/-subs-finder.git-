// sw.js
// Change this string on every deploy (v2, v3, a date, anything new)
const VERSION = 'v1';

const STATIC_CACHE  = `static-${VERSION}`;
const RUNTIME_CACHE = `runtime-${VERSION}`;

const APP_SHELL = [
  './',
  './index.html',
  './assets/favicon.svg',
  './manifest.webmanifest'
];

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(STATIC_CACHE);
    await cache.addAll(APP_SHELL);
    self.skipWaiting();          // activate immediately
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.map(k => {
      if (k !== STATIC_CACHE && k !== RUNTIME_CACHE) return caches.delete(k);
    }));
    await self.clients.claim();  // take control now
  })());
});

// Network-first for HTML (so new UI shows as soon as you publish)
// Cache-first for same-origin assets (fast), with background refresh
self.addEventListener('fetch', (event) => {
  const req = event.request;
  const accept = req.headers.get('accept') || '';

  // HTML pages
  if (req.mode === 'navigate' || accept.includes('text/html')) {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req, { cache: 'no-store' });
        const c = await caches.open(RUNTIME_CACHE);
        c.put(req, fresh.clone());
        return fresh;
      } catch {
        return (await caches.match(req)) || (await caches.match('./index.html'));
      }
    })());
    return;
  }

  // Same-origin assets
  const url = new URL(req.url);
  if (url.origin === location.origin) {
    event.respondWith((async () => {
      const cached = await caches.match(req);
      if (cached) {
        // refresh in background
        fetch(req).then(res => caches.open(RUNTIME_CACHE).then(c => c.put(req, res))).catch(()=>{});
        return cached;
      }
      const res = await fetch(req);
      const c = await caches.open(RUNTIME_CACHE);
      c.put(req, res.clone());
      return res;
    })());
    return;
  }
});
