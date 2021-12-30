const version = "{{VERSION}}",
    site = "{{SITE|safe}}",
    offlinePath = "{{OFFLINE|safe}}",
    assets = {{assets|safe}},
    ignorelist = {{ignorelist|safe}},
    recacheList = {{recacheList|safe}},
    noOfflineList = {{noOfflineList|safe}},
    netFirstList = {{netFirstList|safe}},
    paramRegex = "[a-zA-Z0-9.\\-_?=&%#]";

const staticCacheName = `static-cache-${version}`,
    dynamicCacheName = `dynamic-cache-${version}`;

const testAsteriskPathRegex = (asteriskPath, testPath) => {
    if(testPath.includes('*')) console.warn(testPath, ': includes * while being the testpath')
    if(asteriskPath===testPath) return true;
    const localParamRegex = String(asteriskPath).endsWith("*")
        ? "[a-zA-Z0-9./\\-_?=&%#\:]"
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
        caches.keys().then(async (keys) => {
            return await Promise.all(
                keys.map(async(key) => {
                    return await caches.delete(key)
                })
            ).then(async() => {
                return await caches.open(staticCacheName).then(async(cache) => {
                    return await Promise.all(assets.map(async(asset)=>{ 
                        return await cache.add(asset)
                    }))
                });
            });
        })
    );
});

self.addEventListener("fetch", async (event) => {
    const path = event.request.url.replace(site, "");
    if (
        netFirstList.some((netFirstPath) =>
            testAsteriskPathRegex(netFirstPath, path)
        )
    ) {
        event.respondWith(
            fetch(event.request)
                .then(async (FetchRes) => {
                    if (FetchRes.status < 300) {
                        if (
                            (recacheList.some((recachepath) =>
                                testAsteriskPathRegex(recachepath, path)
                            ) ||
                            event.request.method === "POST") && event.request.headers.get("X-KNOT-RETAIN-CACHE") !== "true"
                        ) {
                            await caches.delete(dynamicCacheName);
                        }
                        const ignore =
                            ignorelist.some((ignorepath) =>
                                testAsteriskPathRegex(ignorepath, path)
                            ) ||
                            noOfflineList.some((noOfflinePath) =>
                                testAsteriskPathRegex(noOfflinePath, path)
                            );
                        if ((!ignore && event.request.method !== "POST") || event.request.headers.get("X-KNOT-ALLOW-CACHE") === "true") {
                            return caches
                                .open(dynamicCacheName)
                                .then((cache) => {
                                    cache.put(
                                        event.request.url,
                                        FetchRes.clone()
                                    );

                                    return FetchRes;
                                });
                        } else {
                            if (
                                FetchRes.redirected &&
                                FetchRes.url.includes("/auth/") &&
                                event.request.url.includes(
                                    FetchRes.url.split("?next=")[1]
                                )
                            ) {
                                throw Error();
                            } else {
                                return FetchRes;
                            }
                        }
                    } else if (FetchRes.status > 300) {
                        if (
                            event.request.headers.get("X-KNOT-REQ-SCRIPT") !==
                            "true"
                        ) {
                            return FetchRes;
                        } else {
                            throw Error();
                        }
                    } else {
                        return caches
                            .match(event.request)
                            .then((cachedResponse) => {
                                if (cachedResponse) {
                                    return cachedResponse;
                                } else throw Error();
                            })
                            .catch(() => {
                                if (
                                    !noOfflineList.find((noOfflinePath) =>
                                        testAsteriskPathRegex(
                                                  noOfflinePath,
                                                  path
                                              )
                                    ) &&
                                    event.request.headers.get(
                                        "X-KNOT-REQ-SCRIPT"
                                    ) !== "true"
                                ) {
                                    return caches.match(offlinePath);
                                }
                            });
                    }
                })
                .catch(() => {
                    return caches
                        .match(event.request)
                        .then((cachedResponse) => {
                            if (cachedResponse) {
                                return cachedResponse;
                            } else throw Error();
                        })
                        .catch(() => {
                            if (
                                !noOfflineList.find((noOfflinePath) =>
                                    testAsteriskPathRegex(
                                              noOfflinePath,
                                              path
                                          )
                                ) &&
                                event.request.headers.get(
                                    "X-KNOT-REQ-SCRIPT"
                                ) !== "true"
                            ) {
                                return caches.match(offlinePath);
                            }
                        });
                })
        );
    } else {
        event.respondWith(
            caches
                .match(event.request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    } else {
                        return fetch(event.request).then(async (FetchRes) => {
                            if (FetchRes.status >= 300) {
                                if (
                                    event.request.method === "GET" &&
                                    event.request.headers.get(
                                        "X-KNOT-REQ-SCRIPT"
                                    ) === "true"
                                ) {
                                    throw Error();
                                }
                                return FetchRes;
                            }
                            if (
                                (recacheList.some((recachepath) =>
                                    testAsteriskPathRegex(
                                              recachepath,
                                              path
                                          )
                                ) ||
                                event.request.method === "POST") && event.request.headers.get("X-KNOT-RETAIN-CACHE") !== "true"
                            ) {
                                await caches.delete(dynamicCacheName);
                            }
                            const ignore =
                                ignorelist.some((ignorepath) =>
                                    testAsteriskPathRegex(
                                              ignorepath,
                                              path
                                          )
                                ) ||
                                noOfflineList.some((noOfflinePath) =>
                                        testAsteriskPathRegex(
                                              noOfflinePath,
                                              path
                                          )
                                );
                            if ((!ignore && event.request.method !== "POST") || event.request.headers.get("X-KNOT-ALLOW-CACHE") === "true") {
                                return caches
                                    .open(dynamicCacheName)
                                    .then((cache) => {
                                        cache.put(
                                            event.request.url,
                                            FetchRes.clone()
                                        );

                                        return FetchRes;
                                    });
                            } else {
                                if (
                                    FetchRes.redirected &&
                                    FetchRes.url.includes("/auth/") &&
                                    event.request.url.includes(
                                        FetchRes.url.split("?next=")[1]
                                    )
                                ) {
                                    throw Error();
                                } else {
                                    return FetchRes;
                                }
                            }
                        });
                    }
                })
                .catch((_) => {
                    if (
                        !noOfflineList.find((noOfflinePath) =>
                            testAsteriskPathRegex(noOfflinePath, path)
                        ) &&
                        event.request.headers.get("X-KNOT-REQ-SCRIPT") !==
                            "true"
                    ) {
                        return caches.match(offlinePath);
                    }
                })
        );
    }
});

self.addEventListener("message", (event) => {
    if (event.data.action === "skipWaiting") {
        self.skipWaiting();
    }
});

self.addEventListener('push', function (event) {
    //https://developer.mozilla.org/en-US/docs/Web/API/PushMessageData.
    const eventInfo = event.data.text();
    // const data = JSON.parse(eventInfo);
    console.log(eventInfo)
    const head = 'Welcome to {{APPNAME}}';
    const body = 'Ready to takeoff? Virtually ofcourse.';

    event.waitUntil(
        self.registration.showNotification(head, {
            body: body,
            icon: '{{SITE|safe}}{{ICON|safe}}'
        })
    );
});

self.addEventListener("cache", (event) => {
  console.log("cache",event)
})