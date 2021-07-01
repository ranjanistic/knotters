subLoader(true);

document.addEventListener("DOMContentLoaded", () => {
    loadGlobalEventListeners()
    loadGlobalEditors();
    loadCarousels({});
});

window.addEventListener("load",()=>{  
    serviceWorkerRegistration();
    subLoader(false);
})
