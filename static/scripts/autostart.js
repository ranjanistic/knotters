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
    loadCarousels({});
    loadBrowsers();
});

window.addEventListener("load", () => {
    getElements("previous-navigation-button").forEach((btn) => {
        btn.addEventListener("click", () => {
            sessionStorage.setItem(Key.navigated, code.LEFT);
        });
    });
    loadReporters();
    loadBrowserSwiper();
    window.history.pushState(
        "object or string",
        document.title,
        window.location.pathname.replace(/'(\?)+[ae]+(\=)+[a-zA-Z0-9]+'/, "")
    );
    serviceWorkerRegistration();
    if (localStorage.getItem(Key.futureMessage)) {
        message(localStorage.getItem(Key.futureMessage));
        localStorage.removeItem(Key.futureMessage);
    }

    if (window.location.host.startsWith("beta.")) {
        getElements("beta-alert-view").forEach((elem) => show(elem));
        if (!window.sessionStorage.getItem("beta-alerted")) betaAlert();
        getElements("hide-beta").forEach((elem) => hide(elem));
    }
    subLoader(false);
    if(sessionStorage.getItem('device-theme')==1){
        message(`Theme set to your system default. Use ${Icon('brightness_medium')} to toggle it.`)
    }
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
        const navbar = getElement("navbar")
        if (__prevScrollpos__ > currentScrollPos) {
            navbar.style.top = "0";
        } else {
            navbar.style.top = `-${navbar.offsetHeight}px`;
        }
        __prevScrollpos__ = currentScrollPos;
    });
})();
