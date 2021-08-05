const newUpdateDialog = (newServiceWorker) => {
    alertify
        .confirm(
            `Update available`,
            `
            <img src="${ICON}" width="50" />
            <h4>A new version of ${APPNAME} is available, with new features & performance improvements.<br/><br/>Shall we update?<h4>
            <h6 class="dead-text">Updates are important. It will take a few seconds.</h6>`,
            () => {
                subLoader(true);
                loader(true);
                message("Updating...");
                localStorage.setItem(Key.appUpdated, 1);
                try {
                    newServiceWorker.postMessage({ action: "skipWaiting" });
                } catch {
                    window.location.reload();
                }
            },
            () => {
                message("We'll remind you later.");
            }
        )
        .set("labels", { ok: `Yes, update now`, cancel: "Not now" })
        .set('transition','flipx')
        .set("closable", false)
        .set("modal", true);
};

const serviceWorkerRegistration = () => {
    if (navigator.serviceWorker) {
        let refreshing = false;
        navigator.serviceWorker.addEventListener("controllerchange", () => {
            if (refreshing) return;
            window.location.reload();
            refreshing = true;
        });
        navigator.serviceWorker
            .register(URLS.SERVICE_WORKER)
            .then((reg) => {
                if (reg.waiting) {
                    const newServiceWorker = reg.waiting;
                    newUpdateDialog(newServiceWorker);
                }
                reg.addEventListener("updatefound", () => {
                    const newServiceWorker = reg.installing;
                    newServiceWorker.addEventListener("statechange", () => {
                        switch (newServiceWorker.state) {
                            case "installed":
                                if (navigator.serviceWorker.controller) {
                                    newUpdateDialog(newServiceWorker);
                                }
                                break;
                        }
                    });
                });
            })
            .catch((err) => console.log("Service worker not registered", err));

        if (Number(localStorage.getItem(Key.appUpdated))) {
            success("App updated successfully.");
            localStorage.removeItem(Key.appUpdated);
        }
    }
};