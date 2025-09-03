// sw.js — cache app + PDF.js for offline
const CACHE = 'subs-finder-v5';
const ASSETS = [
  './', './index.html', './sw.js', './manifest.webmanifest',
  'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js',
  'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js'
];

self.addEventListener('install', (e)=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate', (e)=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
      .then(()=>self.clients.claim())
  );
});
self.addEventListener('fetch', (e)=>{
  const url = new URL(e.request.url);
  const isCDN = /cdn.jsdelivr.net/.test(url.hostname);
  const isSame = url.origin===location.origin;
  if(e.request.method==='GET' && (isSame || isCDN)){
    e.respondWith(
      caches.match(e.request).then(r=> r || fetch(e.request).then(res=>{
        const copy=res.clone(); caches.open(CACHE).then(c=>c.put(e.request, copy));
        return res;
      }))
    );
  }
});
