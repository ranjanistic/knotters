subLoader(true);
serviceWorkerRegistration();

document.addEventListener("DOMContentLoaded", () => {
    loadGlobalEventListeners()
    loadGlobalEditors();
    loadCarousels({});
});

window.addEventListener("load",()=>{  
    subLoader(false);
})
