const version = "{{VERSION}}",
    site = "{{SITE|safe}}",
    offlinePath = "{{OFFLINE|safe}}",
    assets = {{assets|safe}},
    ignorelist = {{ignorelist|safe}},
    recacheList = {{recacheList|safe}},
    noOfflineList = {{noOfflineList|safe}},
    paramRegex = "[a-zA-Z0-9.\\-_?=&%#]";

const staticCacheName = `static-cache-${version}`,
    dynamicCacheName = `dynamic-cache-${version}`;

const testAsteriskPathRegex = (asteriskPath, testPath) => {
    const localParamRegex = String(asteriskPath).endsWith("*")
        ? "[a-zA-Z0-9./\\-_?=&%#]"
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
        caches.keys().then(async(keys) => {
            const prom = Promise.all(keys.map((key) => caches.delete(key))).then(()=>{
                return caches.open(staticCacheName).then((cache) => {
                    return cache.addAll(assets);
                });
            });
            return prom;
        })
    );
});

self.addEventListener("fetch", async (event) => {
    const path = event.request.url.replace(site, "");
    event.respondWith(
        caches
            .match(event.request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                } else {
                    return fetch(event.request).then(async (FetchRes) => {
                        if (FetchRes.status >= 300) {
                            return FetchRes
                        }
                        if (
                            recacheList.some((recachepath) =>
                                recachepath.includes("*")
                                    ? testAsteriskPathRegex(recachepath, path)
                                    : recachepath === path
                            ) || event.request.method === "POST"
                        ) {
                            await caches.delete(dynamicCacheName);
                        }
                        const ignore = ignorelist.some((ignorepath) =>
                            ignorepath.includes("*")
                                ? testAsteriskPathRegex(ignorepath, path)
                                : ignorepath === path
                        ) ||
                            noOfflineList.some((noOfflinePath) =>
                                noOfflinePath.includes("*")
                                    ? testAsteriskPathRegex(noOfflinePath, path)
                                    : noOfflinePath === path
                            )
                            if(!ignore && event.request.method !== "POST"){
                                return caches.open(dynamicCacheName).then((cache) => {
                                      cache.put(
                                          event.request.url,
                                          FetchRes.clone()
                                      );
    
                                      return FetchRes;
                                  });

                            } else {
                                if(FetchRes.redirected && FetchRes.url.includes("/auth/") && event.request.url.includes(FetchRes.url.split('?next=')[1])){
                                    throw Error()
                                } else {
                                    return FetchRes
                                }
                            }
                    });
                }
            })
            .catch((_) => {
                if (
                    !noOfflineList.find((noOfflinePath) =>
                        noOfflinePath.includes("*")
                            ? testAsteriskPathRegex(noOfflinePath, path)
                            : noOfflinePath === path
                    ) && event.request.method !== "POST"
                ) {
                    return caches.match(offlinePath);
                }
            })
    );
});

self.addEventListener("message", (event) => {
    if (event.data.action === "skipWaiting") {
        self.skipWaiting();
    }
});
