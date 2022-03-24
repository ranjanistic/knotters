/**
    Script for autostarting tasks (on page load, document load, window load, etc).
*/

document.addEventListener("DOMContentLoaded", () => {
    if (sessionStorage.getItem(Key.navigated) === code.LEFT) {
        getElementsByTag("html")[0].classList.remove("w3-animate-right");
        getElementsByTag("html")[0].classList.add("w3-animate-left");
        sessionStorage.setItem(Key.navigated, code.RIGHT);
    } else {
        getElementsByTag("html")[0].classList.remove("w3-animate-left");
        getElementsByTag("html")[0].classList.add("w3-animate-right");
    }
    loadGlobalEventListeners();
    loadGlobalEditors();
    loadSnapshotScroller();
    loadDynamicContent();
    loadCarousels({});
    loadBrowsers();
    loadSnapshotActions()
});

window.addEventListener("load", () => {
    getElements("previous-navigation-button").forEach((btn) => {
        btn.addEventListener("click", () => {
            sessionStorage.setItem(Key.navigated, code.LEFT);
        });
    });

    loadReporters();
    loadBrowserSwiper();
    serviceWorkerRegistration();
    clearToastQueue();
    if (localStorage.getItem(Key.futureMessage)) {
        message(localStorage.getItem(Key.futureMessage));
        localStorage.removeItem(Key.futureMessage);
    }

    if (window.location.host.startsWith("beta.")) {
        getElements("beta-alert-view").forEach((elem) => show(elem));
        if (!window.sessionStorage.getItem("beta-alerted")) betaAlert();
        getElements("hide-beta").forEach((elem) => hide(elem));
    }
    if (window.location.href.split("#").length > 1) {
        const elem = getElement(window.location.href.split("#")[1]);
        if (elem) {
            highlightElement(elem);
        }
    }
    window.history.pushState(
        "object or string",
        document.title,
        window.location.pathname.replace(/'(\?)+[ae]+(\=)+[a-zA-Z0-9]+'/, "")
    );
    if (sessionStorage.getItem("device-theme") == 1) {
        message(
            `${STRING.theme_set_sys_default} ${STRING.use} ${Icon(
                "brightness_medium"
            )} ${STRING.to_toggle_it}`
        );
    }
    firstTimeMessage('cookie-alt', `We use cookies to ensure smooth functioning, and by continuing, you agree to our <a class="underline text-accent" href='${setUrlParams(URLS.Docs.TYPE, 'privacypolicy')}' target="_blank">privacy policy & cookie policy</a>.`);
    subLoader(false);
    window.addEventListener("beforeunload",(e)=> {
        subLoader(true);
        return null;
    });
});

addEventListener("keydown", (e) => {
    if (
        (e.key === "F10" || e.code === "F10" || e.keyCode === 121) &&
        e.altKey
    ) {
        toggleTheme();
    }
    if ((e.key === "r" || e.code === "r") && e.altKey) {
        restartIntros();
        window.location.reload();
    }
});

(() => {
    let __prevScrollpos__ = window.pageYOffset;
    window.addEventListener("scroll", () => {
        const currentScrollPos = window.pageYOffset;
        const navbar = getElement("navbar");
        if (__prevScrollpos__ > currentScrollPos) {
            navbar.style.top = "0";
        } else {
            navbar.style.top = `-${navbar.offsetHeight}px`;
        }
        __prevScrollpos__ = currentScrollPos;
    });
})();
