const version = "{{VERSION}}",
	site = "{{SITE|safe}}",
	offlinePath = "{{OFFLINE|safe}}",
	assets = {{assets|safe}},
	ignorelist = {{ignorelist|safe}},
	paramRegex = "[a-zA-Z0-9.\\-_]";

const staticCacheName = `static-cache-${version}`, 
	dynamicCacheName = `dynamic-cache-${version}`;

const testAsteriskPathRegex = (asteriskPath, testPath) => {
    const localParamRegex = String(asteriskPath).endsWith("*")
        ? "[a-zA-Z0-9./\\-_]"
        : paramRegex;
    return RegExp(
        asteriskPath
            .replaceAll("*", `+${localParamRegex}+`)
            .split("+")
            .map((part) =>
                part === localParamRegex ? localParamRegex : `(${part})`
            )
            .join("+") + "$"
    ).test(testPath);
};

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
			const prom = Promise.all(
				keys
				.filter((key) => key !== staticCacheName)
				.map((key) => caches.delete(key))
			);
			caches.open(staticCacheName).then((cache) => {
				return cache.addAll(assets);
			})
			return prom
		})
    );
});

self.addEventListener("fetch", (event) => {
    const path = event.request.url.replace(site, "");
    if (!(event.request.url.indexOf("http") === 0)) return;
    event.respondWith(
        caches
            .match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                } else {
                    return fetch(event.request).then((FetchRes) => {
                        return ignorelist.some((ignorepath) =>
                            ignorepath.includes("*")
                                ? testAsteriskPathRegex(ignorepath, path)
                                : ignorepath === path
                        )
                            ? FetchRes
                            : caches.open(dynamicCacheName).then((cache) => {
                                  cache.put(
                                      event.request.url,
                                      FetchRes.clone()
                                  );
                                  return FetchRes;
                              });
                    });
                }
            })
            .catch((_) => {
				if(!path.toLowerCase().includes('tab')){
					return caches.match(offlinePath)
				}
			})
    );
});

self.addEventListener("message", (event) => {
    if (event.data.action === "skipWaiting") {
        self.skipWaiting();
    }
});
