const _VERSION = "{{VERSION}}",
    _SITE = "{{SITE|safe}}",
    _DEBUG = "{{DEBUG}}" == "True",
    _OFFPATH = "{{OFFLINE|safe}}",
    X_ALLOWCACHE = "X-KNOT-ALLOW-CACHE",
    X_RETAINCACHE = "X-KNOT-RETAIN-CACHE",
    X_SCRIPTFETCH = "X-KNOT-REQ-SCRIPT",
    _PARAMREGEX = "[a-zA-Z0-9./\\-_?=&%#:@]";

const _STAT_CACHE_NAME = `static-cache-${_VERSION}`,
    _DYN_CACHE_NAME = `dynamic-cache-${_VERSION}`;

const EVENTS = {
    ACTIVATE: "activate",
    FETCH: "fetch",
    MESSAGE: "message",
};
const METHODS = {
    GET: "GET",
    POST: "POST",
};

const H_TRUE = "true";
const H_FALSE = "false";

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
    if (asteriskPath === testPath) return true;
    return RegExp(
        asteriskPath
            .replaceAll("*", `+${_PARAMREGEX}+`)
            .split("+")
            .map((part) => (part === _PARAMREGEX ? _PARAMREGEX : `(${part})`))
            .join("+") + "$"
    ).test(testPath);
};


const canClearDynCache = (path, event) => {
    // will always clear dyn cache if POST method, except if retain cache header is true
    return (
        (event.request.method === METHODS.POST &&
            event.request.headers.get(X_RETAINCACHE) !== H_TRUE)
    );
};

const canSetDynCache = (path, event) => {
    // will never set dyn cache if POST method, except if allow cache header is true
    return (
        event.request.method !== METHODS.POST ||
            event.request.headers.get(X_ALLOWCACHE) == H_TRUE
    );
};

const canShowOfflineView = (path, event) => {
    return !(
        event.request.headers.get(X_SCRIPTFETCH) == H_TRUE
    );
};

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

const cacheFetchResponseHandler = async (path, event, CachedRes) => {
    let FetchRes;
    if(!canShowOfflineView(path, event)) {
        try{
            FetchRes = await fetch(event.request);
        } catch {
            if (CachedRes){
                {% if DEBUG %}debug_log(`${path} is cached`);{% endif %}
                return CachedRes;
            }        
        }
    } else if (CachedRes) {
        {% if DEBUG %}debug_log(`${path} is cached`);{% endif %}
        return CachedRes;
    }
    
    {% if DEBUG %}debug_log(`${path} is not cached`);{% endif %}
    if(!FetchRes){
        FetchRes = await fetch(event.request);
    }
    {% if DEBUG %}debug_log(`${path} is fetched`, FetchRes.status);{% endif %}
    if (FetchRes.status < 300) {
        if (canClearDynCache(path, event)) {
            {% if DEBUG %}debug_log(`${path} can clear dyn cache`);{% endif %}
            await caches.delete(_DYN_CACHE_NAME);
        }
        if (canSetDynCache(path, event)) {
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
        {% if DEBUG %}debug_log(`${path} is not a redirect to auth`);{% endif %}
        return FetchRes;
    } else if (FetchRes.status < 400) {
        {% if DEBUG %}debug_log(`${path} status under 400`);{% endif %}
        if (event.request.headers.get(X_SCRIPTFETCH) !== H_TRUE) {
            return FetchRes;
        }
        throw Error(event);
    } else {
        throw Error(event);
    }
};

const cacheFetchErrorHandler = async (path, event, error) => {
    {% if DEBUG %}debug_log(`${path} cachefetch error`);{% endif %}
    if (canShowOfflineView(path, event)) {
        {% if DEBUG %}debug_log(`${path} can show offline`);{% endif %}
        return caches.match(_OFFPATH);
    }
    {% if DEBUG %}debug_log(`${path} cannot show offline`);{% endif %}
    console.log(error);
};

self.addEventListener(EVENTS.FETCH, async (event) => {
    const path = event.request.url.replace(_SITE, "");
    event.respondWith(
        caches.match(event.request).then(async(CachedRes)=>{
            return await cacheFetchResponseHandler(path,event, CachedRes)
        }).catch(async(e)=>{
            return await cacheFetchErrorHandler(path, event, e)
        })
    );
});

self.addEventListener(EVENTS.MESSAGE, (event) => {
    if (event.data.action === "skipWaiting") {
        self.skipWaiting();
    }
});
