const _VERSION = "{{VERSION}}",
    _SITE = "{{SITE|safe}}",
    _DEBUG = "{{DEBUG}}" == "True",
    _OFFPATH = "{{OFFLINE|safe}}",
    X_ALLOWCACHE = "X-KNOT-ALLOW-CACHE",
    X_RETAINCACHE = "X-KNOT-RETAIN-CACHE",
    X_SCRIPTFETCH = "X-KNOT-REQ-SCRIPT",
    ASSETS = {{assets|safe}},
    IGNORELIST = {{ignorelist|safe}},
    RECACHELIST = {{recacheList|safe}},
    NOOFFLINELIST = {{noOfflineList|safe}},
    NETFIRSTLIST = {{netFirstList|safe}},
    PARAMREGEX = "[a-zA-Z0-9./\\-?=&%#:@]",
    _STAT_CACHE_NAME = `static-cache-${_VERSION}`,
    _DYN_CACHE_NAME = `dynamic-cache-${_VERSION}`,
    EVENTS = {
        ACTIVATE: "activate",
        FETCH: "fetch",
        MESSAGE: "message",
        PUSH: "push",
    },
    METHODS = {
        GET: "GET",
        POST: "POST",
    },
    H_TRUE = "true",
    H_FALSE = "false";

{% if DEBUG %}
const debug_log = (l) => {
    if (_DEBUG && !(l.startsWith("/media") || l.startsWith("/static"))) {
        console.log(l);
    }
};
{% endif %}

const testAsteriskPathRegex = (asteriskPath, testPath) => {
    {% if DEBUG %}
    if (testPath.includes("*"))
        debug_log(testPath, ": includes * while being the testpath");
    {% endif %}
    testPath = testPath.split("?")[0];
    if (asteriskPath === testPath) return true;
    return RegExp(
        `^${asteriskPath}`
            .replaceAll("*", `+${_PARAMREGEX}+`)
            .split("+")
            .map((part) =>
                part === _PARAMREGEX ? _PARAMREGEX : part ? `(${part})` : ""
            )
            .join("+") + "$"
    ).test(testPath);
};

const isNetFirst = (path) =>
        NETFIRSTLIST.some((netFirst) =>
            testAsteriskPathRegex(netFirst, path)
        ),
    isNoOffline = (path) =>
        NOOFFLINELIST.some((noOffline) =>
            testAsteriskPathRegex(noOffline, path)
        ),
    isIgnored = (path) =>
        IGNORELIST.some((ignore) => testAsteriskPathRegex(ignore, path)),
    isRecache = (path) =>
        RECACHELIST.some((recache) => testAsteriskPathRegex(recache, path)),
    // will always clear dyn cache if POST method, except if retain cache header is true
    canClearDynCache = (path, event) =>
        isRecache(path) ||
        (event.request.method === METHODS.POST &&
            event.request.headers.get(X_RETAINCACHE) !== H_TRUE),
    // will never set dyn cache if POST method, except if allow cache header is true
    canSetDynCache = (path, event) =>
        !isIgnored(path) &&
        (event.request.method !== METHODS.POST ||
            event.request.headers.get(X_ALLOWCACHE) == H_TRUE),
    canShowOfflineView = (path, event) =>
        !(
            isNoOffline(path) ||
            event.request.headers.get(X_SCRIPTFETCH) == H_TRUE
        );

// To add static ASSETS in static cache DB on service worker installation/update
self.addEventListener(EVENTS.ACTIVATE, (event) =>
    event.waitUntil(
        caches
            .keys()
            .then(
                async (keys) =>
                    await Promise.all(
                        keys
                            .filter((key) => key != _STAT_CACHE_NAME)
                            .map(async (key) => await caches.delete(key))
                    )
                        .then(
                            async (_) =>
                                await caches
                                    .open(_STAT_CACHE_NAME)
                                    .then(
                                        async (cache) =>
                                            await Promise.all(
                                                ASSETS.map(async (asset) => {
                                                    const matched =
                                                        await cache.match(
                                                            asset
                                                        );
                                                    if (
                                                        !(
                                                            matched &&
                                                            matched.status ===
                                                                200
                                                        )
                                                    ) {
                                                        try {
                                                            await cache.add(
                                                                asset
                                                            );
                                                        } catch (e) {
                                                            {% if DEBUG %}debug_log(`static: ${asset} not added: ${e}`);{% endif %}
                                                        }
                                                    }
                                                })
                                            )
                                    )
                                    .catch((e) => {
                                        console.error(e);
                                        return caches.delete(_STAT_CACHE_NAME);
                                    })
                        )
                        .catch((err) => {
                            console.error(err);
                            return err;
                        })
            )
            .catch((err) => {
                console.error(err);
                return err;
            })
    )
);

// To handle network fetched responses
const netFetchResponseHandler = async (path, event, FetchRes) => {
    if (FetchRes.status < 300) {
        if (canClearDynCache(path, event)) {
            {% if DEBUG %}debug_log(`${path} can clear dyn cache`);{% endif %}
            await caches.delete(_DYN_CACHE_NAME);
        }
        if (ASSETS.includes(path)) {
            {% if DEBUG %}debug_log(`${path} is static asset`);{% endif %}
            try {
                const cache = await caches.open(_STAT_CACHE_NAME);
                cache.put(event.request.url, FetchRes.clone());
                return FetchRes;
            } catch (e) {
                console.error(e);
                return FetchRes;
            }
        } else if (canSetDynCache(path, event)) {
            {% if DEBUG %}debug_log(`${path} can set cache`);{% endif %}
            try {
                const cache = await caches.open(_DYN_CACHE_NAME);
                cache.put(event.request.url, FetchRes.clone());
                return FetchRes;
            } catch (e) {
                console.error(e);
                return FetchRes;
            }
        }
        {% if DEBUG %}debug_log(`${path} does not allow set caching`);{% endif %}
        {% if DEBUG %}debug_log(`${path} is ignored: ${isIgnored(path)}`);{% endif %}
        if (FetchRes.redirected && FetchRes.url.includes("/auth/")) {
            {% if DEBUG %}debug_log(`${path} is a redirect to auth`);{% endif %}
            const splitnext = FetchRes.url.split("?next=");
            if (
                splitnext.length > 1 &&
                event.request.url.includes(splitnext[1])
            ) {
                {% if DEBUG %}debug_log(`${path} redirect to auth with next`);{% endif %}
                throw Error(event.request.url);
            }
            {% if DEBUG %}debug_log(`${path} redirect to auth without next`);{% endif %}
        }
        return FetchRes;
    } else if (FetchRes.status < 400) {
        {% if DEBUG %}debug_log(`${path} status under 400`);{% endif %}
        if (event.request.headers.get(X_SCRIPTFETCH) !== H_TRUE) {
            return FetchRes;
        }
        throw Error(event);
    } else if (FetchRes.status == 404) {
        if (event.request.headers.get(X_SCRIPTFETCH) !== H_TRUE) {
            return FetchRes;
        }
    }
    throw Error(event);
};

// To handle network fetched responses error
const netFetchErrorHandler = async (path, event, error) => {
    {% if DEBUG %}debug_log(`${path} netfecth error`);{% endif %}
    try {
        const cachedResponse = await caches.match(event.request.url);
        if (!cachedResponse) {
            throw Error(event);
        }
        {% if DEBUG %}debug_log(`${path} is cached`);{% endif %}
        return cachedResponse;
    } catch (e) {
        {% if DEBUG %}debug_log(`${path} is not cached`);{% endif %}
        if (canShowOfflineView(path, event)) {
            {% if DEBUG %}debug_log(`${path} can show offline`);{% endif %}
            return caches.match(_OFFPATH);
        }
        {% if DEBUG %}debug_log(`${path} cannot show offline`);{% endif %}
        console.log(error);
    }
};

// To handle cache fetched responses
const cacheFetchResponseHandler = async (path, event, CachedRes) => {
    if (CachedRes) {
        {% if DEBUG %}debug_log(`${path} is cached`);{% endif %}
        return CachedRes;
    }
    {% if DEBUG %}debug_log(`${path} is not cached`);{% endif %}
    const FetchRes = await fetch(event.request);
    {% if DEBUG %}debug_log(`${path} is fetched`, FetchRes.status);{% endif %}
    if (FetchRes.status >= 300) {
        if (
            event.request.method === METHODS.GET &&
            event.request.headers.get(X_SCRIPTFETCH) === H_TRUE
        ) {
            // get script fetch error can show offline view
            throw Error(event.request.url);
        }
        {% if DEBUG %}debug_log(`${path} is not fetched`, FetchRes.status);{% endif %}
        return FetchRes;
    }
    if (canClearDynCache(path, event)) {
        {% if DEBUG %}debug_log(`${path} can clear dyn cache`);{% endif %}
        await caches.delete(_DYN_CACHE_NAME);
    }
    if (ASSETS.includes(path)) {
        {% if DEBUG %}debug_log(`${path} is static asset`);{% endif %}
        try {
            const cache = await caches.open(_STAT_CACHE_NAME);
            cache.put(event.request.url, FetchRes.clone());
            return FetchRes;
        } catch (e) {
            console.error(e);
        }
    } else if (canSetDynCache(path, event)) {
        {% if DEBUG %}debug_log(`${path} can set dyn cache`);{% endif %}
        try {
            const cache = await caches.open(_DYN_CACHE_NAME);
            cache.put(event.request.url, FetchRes.clone());
        } catch (e) {
            console.error(e);
        }
    }
    if (FetchRes.redirected && FetchRes.url.includes("/auth/")) {
        {% if DEBUG %}debug_log(`${path} is a redirect to auth`);{% endif %}
        const splitnext = FetchRes.url.split("?next=");
        if (splitnext.length > 1 && event.request.url.includes(splitnext[1])) {
            {% if DEBUG %}debug_log(`${path} redirect to auth with next`);{% endif %}
            throw Error(event.request.url);
        }
    }
    return FetchRes;
};

// To handle cache fetched responses error
const cacheFetchErrorHandler = async (path, event, error) => {
    {% if DEBUG %}debug_log(`${path} cachefetch error`);{% endif %}
    if (canShowOfflineView(path, event)) {
        {% if DEBUG %}debug_log(`${path} can show offline`);{% endif %}
        return caches.match(_OFFPATH);
    }
    {% if DEBUG %}debug_log(`${path} cannot show offline`);{% endif %}
    console.log(error);
};

// To add requests responses in dynamic cache DB, depending upon request path & response status
self.addEventListener(EVENTS.FETCH, async (event) => {
    const path = event.request.url.replace(_SITE, "");
    if (isNetFirst(path)) {
        event.respondWith(
            fetch(event.request)
                .then(
                    async (FetchRes) =>
                        await netFetchResponseHandler(path, event, FetchRes)
                )
                .catch(async (e) => await netFetchErrorHandler(path, event, e))
        );
    } else {
        event.respondWith(
            caches
                .match(event.request)
                .then(
                    async (CachedRes) =>
                        await cacheFetchResponseHandler(path, event, CachedRes)
                )
                .catch(
                    async (e) => await cacheFetchErrorHandler(path, event, e)
                )
        );
    }
});

// To proceed with service worker installation/update
self.addEventListener(EVENTS.MESSAGE, (event) => {
    if (event.data.action === "skipWaiting") {
        self.skipWaiting();
    }
});

// For web push messages
self.addEventListener(EVENTS.PUSH, (event) => {
    const payload = event.data
        ? event.data.text()
        : JSON.stringify({ title: "{{APPNAME}}" });
    console.log(payload)
    const defaultOps = {
        url: null,
        icon: "{{ICON_PNG}}",
        badge: "{{ICON_SHADOW_PNG}}",
        actions: [],
        dir: "auto",
        image: null,
        lang: "en",
        renotify: false,
        requireInteraction: false,
        silent: false,
        tag: "{{APPNAME}}{{VERSION}}",
        timestamp: Date.now(),
        vibrate: [200, 100, 200],
    };
    let title,
        options = defaultOps;
    try {
        (data = JSON.parse(payload)), (title = data.title);
        options = {
            body: data.body || "",
            url: data.url || defaultOps.url,
            icon: data.icon || defaultOps.icon,
            badge: data.badge || defaultOps.badge,
            actions: data.actions || defaultOps.actions,
            dir: data.dir || defaultOps.dir,
            image: data.image || defaultOps.image,
            lang: data.lang || defaultOps.lang,
            renotify: data.renotify || defaultOps.renotify,
            requireInteraction:
                data.requireInteraction || defaultOps.requireInteraction,
            silent: data.silent || defaultOps.silent,
            tag: data.tag || defaultOps.tag,
            timestamp: data.timestamp || defaultOps.timestamp,
            vibrate: data.vibrate || defaultOps.vibrate,
        };
    } catch {
        title = payload;
    }
    {% if DEBUG %}debug_log(title);{% endif %}
    event.waitUntil(self.registration.showNotification(title, options));
});
self.addEventListener('notificationclick', function(event) {
    console.log('On notification click: ', event.notification);
    clients.openWindow(event.action);
    event.notification.close();
  });