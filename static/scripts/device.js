/**
 * Client device/browser related controls & settings
 */

window.addEventListener("beforeinstallprompt", (e) => {
    __appInstallPromptEvent = e;
});

window.addEventListener("appinstalled", () => {
    installWebAppInstructions(false);
    __appInstallPromptEvent = null;
    success(STRING.app_install_success);
});

const __clearCacheByPath__ = async (path) => {
    if (!path) return false;
    let cache = await caches.open(STRING.dynamic_cache_name);
    let keys = await cache.keys();
    let data = await Promise.all(
        keys.map((key) => {
            if (key.url.indexOf(path) > -1) {
                return cache.delete(key, { ignoreSearch: true });
            }
        })
    );
    if (data && data.length > 0) {
        return true;
    } else {
        cache = await caches.open(STRING.static_cache_name);
        keys = await cache.keys();
        data = await Promise.all(
            keys.map((key) => {
                if (key.url.indexOf(path) > -1) {
                    return cache.delete(key, { ignoreSearch: true });
                }
            })
        );
        if (data && data.length > 0) {
            return true;
        }
        return false;
    }
};

const __clearDynamicCache__ = async () => {
    await caches.delete(STRING.dynamic_cache_name);
};
const __clearStaticCache__ = async () => {
    await caches.delete(STRING.static_cache_name);
};

const __clearAllCache__ = async () => {
    await caches.delete(STRING.dynamic_cache_name);
    await caches.delete(STRING.static_cache_name);
};

const windowScrollState = (enable = true) => {
    var keys = { 37: 1, 38: 1, 39: 1, 40: 1 };

    function preventDefault(e) {
        e.preventDefault();
    }

    function preventDefaultForScrollKeys(e) {
        if (keys[e.keyCode]) {
            preventDefault(e);
            return false;
        }
    }

    var supportsPassive = false;
    try {
        window.addEventListener(
            "test",
            null,
            Object.defineProperty({}, "passive", {
                get: function () {
                    supportsPassive = true;
                },
            })
        );
    } catch (e) {}

    var wheelOpt = supportsPassive ? { passive: false } : false;
    var wheelEvent =
        "onwheel" in document.createElement("div") ? "wheel" : "mousewheel";

    function disableScroll() {
        window.addEventListener("DOMMouseScroll", preventDefault, false); // older FF
        window.addEventListener(wheelEvent, preventDefault, wheelOpt); // modern desktop
        window.addEventListener("touchmove", preventDefault, wheelOpt); // mobile
        window.addEventListener("keydown", preventDefaultForScrollKeys, false);
    }

    function enableScroll() {
        window.removeEventListener("DOMMouseScroll", preventDefault, false);
        window.removeEventListener(wheelEvent, preventDefault, wheelOpt);
        window.removeEventListener("touchmove", preventDefault, wheelOpt);
        window.removeEventListener(
            "keydown",
            preventDefaultForScrollKeys,
            false
        );
    }
    enable ? enableScroll() : disableScroll();
};

const isStandaloneMode = (_) =>
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone ||
    document.referrer.includes("android-app://");

const canInstallPWA = (_) => (window.navigator.serviceWorker ? true : false);

const refresh = ({ fullLoad = false, subload = true }) => {
    if (subload) subLoader(subload);
    if (fullLoad) loader(fullLoad);
    window.location.reload();
};

const refer = ({
    path = window.location.pathname,
    query = {},
    fullLoad = false,
    subload = true,
}) => {
    if (path.startsWith("http") && !path.startsWith(SITE)) {
        newTab(setUrlQueries(path, query));
    } else {
        if (subload) subLoader(subload);
        if (fullLoad) loader(fullLoad);
        window.location.href = setUrlQueries(path, query);
    }
};

const relocate = ({
    path = window.location.pathname,
    query = {},
    fullLoad = false,
    subload = true,
}) => {
    if (path.startsWith("http") && !path.startsWith(SITE)) {
        newTab(setUrlQueries(path, query));
    } else {
        if (subload) subLoader(subload);
        if (fullLoad) loader(fullLoad);
        window.location.replace(setUrlQueries(path, query));
    }
};
