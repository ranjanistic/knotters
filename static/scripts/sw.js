const newUpdateDialog = async (newServiceWorker) => {
    if (sessionStorage.getItem(Key.deferupdate) != 1) {
        Swal.fire({
            title: STRING.update_available,
            imageUrl: isDark() ? ICON_DARK : ICON,
            imageWidth: 90,
            html: `
            <div class="w3-row w3-center id="app-update-view">
            <h5 class="text-primary">A new version of ${APPNAME} is available,<br/> with new features <br/>& performance improvements.</h5>
            <strong class="align">v<span id="app-update-view-oldversion">...</span>&nbsp;${Icon(
                "fast_forward"
            )}&nbsp;v<span class="positive-text" id="app-update-view-newversion">...</span></strong>
            <h4>Shall we update?</h4>
            <h6 class="dead-text">Updates are important. It will take a few seconds, depending upon your network strength.</h6>
            </div>`,
            showDenyButton: true,
            showConfirmButton: true,
            confirmButtonText: "Yes, update now",
            denyButtonText: "No, not now",
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
                message("Updating...");
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
                message("Okay, we won't remind you in this session.");
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
                initializePushNotification(reg);
            })
            .catch((err) => {
                console.log("SW:0:", err);
                error(
                    "An internal error occurred. We humbly request you to reload this page."
                );
            });

        if (Number(localStorage.getItem(Key.appUpdated))) {
            success("App updated successfully.");
            localStorage.removeItem(Key.appUpdated);
        }
    } else {
        message(
            "Your browser doesn't support some of our features ☹️. Please update/change your browser for the best experience."
        );
    }
};

const initializePushNotification = (reg) => {
    reg.pushManager.getSubscription().then((subscription) => {
        if (subscription) {
            togglePushSubscription({
                statusType: "subscribe",
                subscription,
                // callback: (response) => {
                //     if (response) {
                //         message(
                //             "Successfully subscribed for Push Notification"
                //         );
                //     }
                // },
            });
        }
    });
};
