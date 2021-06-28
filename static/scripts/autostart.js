subLoader(true);
serviceWorkerRegistration();

document.addEventListener("DOMContentLoaded", () => {
    loadGlobalEventListeners()
    loadGlobalEditors();
});

window.addEventListener("load",()=>{  
    subLoader(false);
})
