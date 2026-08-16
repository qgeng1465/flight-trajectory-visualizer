/* ✈ 飞行足迹 · Flight Footprints — offline cache (privacy-first: nothing leaves the browser) */
const CACHE = 'flight-footprints-v12';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './sample.csv',
  './airports.csv',
  './countries.geojson',
  './earth.jpg',
  './earth-topology.png',
  './icon-192.png',
  './icon-512.png',
  './likes.jpg',
  './libs/three.min.js',
  './libs/globe.gl.min.js',
  './libs/papaparse.min.js',
  './libs/topojson-client.min.js',
  './libs/Stats.min.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then((c) => Promise.all(ASSETS.map((a) => c.add(a).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  if (new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const cp = res.clone();
          caches.open(CACHE).then((c) => c.put(req, cp)).catch(() => {});
          return res;
        })
        .catch(() => caches.match('./index.html'))
    );
    return;
  }
  e.respondWith(
    caches.match(req).then((hit) =>
      hit ||
      fetch(req).then((res) => {
        const cp = res.clone();
        caches.open(CACHE).then((c) => c.put(req, cp)).catch(() => {});
        return res;
      })
    )
  );
});
