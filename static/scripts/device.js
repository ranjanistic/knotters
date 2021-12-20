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


const windowScrollState =(enable=true) => {

    var keys = {37: 1, 38: 1, 39: 1, 40: 1};

    function preventDefault(e) {
    e.preventDefault();
    }

    function preventDefaultForScrollKeys(e) {
    if (keys[e.keyCode]) {
        preventDefault(e);
        return false;
    }
    }

    // modern Chrome requires { passive: false } when adding event
    var supportsPassive = false;
    try {
    window.addEventListener("test", null, Object.defineProperty({}, 'passive', {
        get: function () { supportsPassive = true; } 
    }));
    } catch(e) {}

    var wheelOpt = supportsPassive ? { passive: false } : false;
    var wheelEvent = 'onwheel' in document.createElement('div') ? 'wheel' : 'mousewheel';

    // call this to Disable
    function disableScroll() {
        window.addEventListener('DOMMouseScroll', preventDefault, false); // older FF
        window.addEventListener(wheelEvent, preventDefault, wheelOpt); // modern desktop
        window.addEventListener('touchmove', preventDefault, wheelOpt); // mobile
        window.addEventListener('keydown', preventDefaultForScrollKeys, false);
    }

    function enableScroll() {
        window.removeEventListener('DOMMouseScroll', preventDefault, false);
        window.removeEventListener(wheelEvent, preventDefault, wheelOpt); 
        window.removeEventListener('touchmove', preventDefault, wheelOpt);
        window.removeEventListener('keydown', preventDefaultForScrollKeys, false);
    }
    enable ? enableScroll(): disableScroll();
}