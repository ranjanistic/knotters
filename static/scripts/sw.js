const newUpdateDialog = async (newServiceWorker) => {
    if (sessionStorage.getItem(Key.deferupdate) != 1) {
        Swal.fire({
            title: STRING.update_available,
            imageUrl: isDark() ? ICON_DARK : ICON,
            imageWidth: 90,
            html: `<div class="w3-row w3-center id="app-update-view">
            <h5 class="text-primary">${
                STRING.app_new_version_available
            },<br/> ${STRING.with_new_features} <br/>& ${
                STRING.perf_improvements
            }.</h5>
            <strong class="align">v<span id="app-update-view-oldversion">...</span>&nbsp;${Icon(
                "fast_forward"
            )}&nbsp;v<span class="positive-text" id="app-update-view-newversion">...</span></strong>
            <h4>${STRING.shall_we_update}</h4>
            <h6 class="dead-text">${STRING.updates_are_imp} ${
                STRING.will_take_few_seconds
            }</h6>
            </div>`,
            showDenyButton: true,
            showConfirmButton: true,
            confirmButtonText: STRING.yes_up_now,
            denyButtonText: STRING.not_now,
            allowOutsideClick: false,
            didOpen: async () => {
                const newversion = await getRequest2({
                    path: URLS.VERSION_TXT,
                });
                let oldversion = VERSION;
                if (oldversion == newversion) {
                    let vchars = String(
                        Number(oldversion.replaceAll(".", "")) - 1
                    ).split("");
                    if (vchars.length > 3) {
                        const rest = vchars.splice(0, vchars.length - 2);
                        oldversion = rest.join("") + "." + vchars.join(".");
                    } else {
                        oldversion = vchars.join(".");
                    }
                }
                getElement("app-update-view-oldversion").innerHTML = oldversion;
                getElement("app-update-view-newversion").innerHTML = newversion;
            },
        }).then(async (result) => {
            if (result.isDismissed) return;
            if (result.isConfirmed) {
                sessionStorage.removeItem(Key.deferupdate);
                subLoader(true);
                loader(true);
                message(STRING.updating);
                localStorage.setItem(Key.appUpdated, 1);
                try {
                    newServiceWorker.postMessage({ action: "skipWaiting" });
                } catch {
                    window.location.reload();
                }
                return;
            }
            if (result.isDenied) {
                sessionStorage.setItem(Key.deferupdate, 1);
                show(getElement("new-update-action"), false);
                getElement("new-update-action").onclick = (_) => {
                    sessionStorage.removeItem(Key.deferupdate);
                    newUpdateDialog(newServiceWorker);
                };
                message(STRING.update_supressed);
            }
        });
    } else {
        getElement("new-update-action").onclick = (_) => {
            sessionStorage.removeItem(Key.deferupdate);
            newUpdateDialog(newServiceWorker);
        };
        show(getElement("new-update-action"), false);
    }
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
                if (authenticated) {
                    initializePushNotification(reg);
                }
            })
            .catch((err) => {
                console.log("SW:0:", err);
                console.log(STRING.internal_error);
            });

        if (Number(localStorage.getItem(Key.appUpdated))) {
            success(STRING.app_update_success);
            localStorage.removeItem(Key.appUpdated);
        }
    } else {
        message(STRING.browser_outdated);
    }
};
const _notifyServiceWorkerRegistration = () => {
    if (navigator.serviceWorker) {
        navigator.serviceWorker
            .register(URLS.Auth.NOTIFY_SW)
            .then((reg) => {
                console.log(reg);
                if (reg.waiting) {
                    reg.waiting.postMessage({ action: "skipWaiting" });
                }
                reg.addEventListener("updatefound", () => {
                    if (reg.waiting) {
                        reg.waiting.postMessage({ action: "skipWaiting" });
                    }
                });
                initializePushNotification(reg);
            })
            .catch((err) => {
                console.log("NSW:0:", err);
            });
    }
};

const initializePushNotification = (reg) => {
    reg.pushManager.getSubscription().then((subscription) => {
        if (subscription) {
            togglePushSubscription({
                statusType: "subscribe",
                subscription,
            });
        }
    });
};
