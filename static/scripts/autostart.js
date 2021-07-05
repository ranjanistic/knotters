subLoader(true);

document.addEventListener("DOMContentLoaded", () => {
    loadGlobalEventListeners();
    loadGlobalEditors();
    loadCarousels({});
});

window.addEventListener("load", () => {
    loadReporters();
    subLoader(false);
    window.history.pushState('object or string', document.title, window.location.pathname.replace(/'(\?)+[ae]+(\=)+[a-zA-Z0-9]+'/,''))
    serviceWorkerRegistration();
});
