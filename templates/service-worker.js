const staticCacheName = "static-pages-cache";
const dynamicCacheName = "dynamic-pages-cache";

const assets = [
  "/",
  "/compete/",
  "/people/",
  "/projects/",
  "/static/styles/index.css",
  "/static/styles/theme.css",
  "/static/styles/scrollbar.css",
  "/static/styles/loader.css",
  "/static/styles/w3.css",
  "/static/scripts/index.js",
  "/static/scripts/theme.js",
];

self.addEventListener("install", (event) => {
  console.log("Service worker installed!!");

  event.waitUntil(
    caches.open(staticCacheName).then((cache) => {
      console.log("caching in  process");
      return cache.addAll(assets);
    })
  );
});

self.addEventListener("activate", (event) => {
  console.log("Service worker activated!!");

  event.waitUntil(
    caches.keys().then((keys) => {
      console.log(keys);
      return Promise.all(
        keys
          .filter((key) => key !== staticCacheName)
          .map((key) => caches.delete(key))
      );
    })
  );
});

self.addEventListener("fetch", (event) => {
  console.log("Fetch intercepted for:", event.request.url);
  if (!(event.request.url.indexOf("http") === 0)) return;
  event.respondWith(
    caches
      .match(event.request)
      .then((cachedResponse) => {
        if (cachedResponse) {
          console.log("Found:", event.request.url, "in cache");
          return cachedResponse;
        } else {
          console.log("Network request for:", event.request.url);
          return fetch(event.request).then((FetchRes) => {
            return caches.open(dynamicCacheName).then((cache) => {
              cache.put(event.request.url, FetchRes.clone());
              return FetchRes;
            });
          });
        }
      })
      .catch((err) => console.log("error", err))
  );
});
