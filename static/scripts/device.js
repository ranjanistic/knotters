/**
 * Client device/browser related controls & settings
 */

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
