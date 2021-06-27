subLoader(true);
serviceWorkerRegistration();

document.addEventListener("DOMContentLoaded", () => {
    loadGlobalEventListeners()
});

window.addEventListener("load",()=>{  
    subLoader(false);
})
