/* Service worker do app do aluno. Guarda somente a casca do app; dados pessoais (/api) nunca são armazenados. */
const CACHE = "minhas-aulas-{{ versao }}";
const CASCA = [
  "/app/",
  "/app/manifest.webmanifest",
  "/static/app_aluno/app.css?v={{ versao }}",
  "/static/app_aluno/app.js?v={{ versao }}",
  "/static/app_aluno/icon.svg",
  "/static/app_aluno/apple-touch-icon.png"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((chaves) => Promise.all(chaves.filter((chave) => chave !== CACHE).map((chave) => caches.delete(chave))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) {
    return;
  }
  if (event.request.mode === "navigate") {
    event.respondWith(fetch(event.request).catch(() => caches.match("/app/")));
    return;
  }
  if (url.pathname.startsWith("/static/app_aluno/") || url.pathname === "/app/manifest.webmanifest") {
    event.respondWith(caches.match(event.request).then((resposta) => resposta || fetch(event.request)));
  }
});
