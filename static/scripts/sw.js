const newUpdateDialog = async (newServiceWorker) => {
    if(sessionStorage.getItem(Key.deferupdate)!=1){
        Swal.fire({
            title: STRING.update_available,
            imageUrl: isDark()?ICON_DARK:ICON,
            imageWidth: 90,
            html: `
            <div class="w3-row w3-center id="app-update-view">
            <h5 class="text-primary">A new version of ${APPNAME} is available,<br/> with new features <br/>& performance improvements.</h5>
            <strong class="align">v<span id="app-update-view-oldversion">...</span>&nbsp;${Icon('fast_forward')}&nbsp;v<span class="positive-text" id="app-update-view-newversion">...</span></strong>
            <h4>Shall we update?</h4>
            <h6 class="dead-text">Updates are important. It will take a few seconds, depending upon your network strength.</h6>
            </div>`,
            showDenyButton: true,
            showConfirmButton: true,
            confirmButtonText: 'Yes, update now',
            denyButtonText: 'No, not now',
            allowOutsideClick: false,
            didOpen: async () => {
                const newversion = await getRequest2({path:URLS.VERSION_TXT})
                let oldversion = VERSION;
                if(oldversion == newversion){
                    let vchars = String(Number(oldversion.replaceAll('.','')) - 1).split('');
                    if(vchars.length > 3){
                        const rest = vchars.splice(0, vchars.length-2)
                        oldversion = rest.join('') + '.' + vchars.join('.')
                    } else {
                        oldversion = vchars.join('.')
                    }
                }
                getElement("app-update-view-oldversion").innerHTML = oldversion;
                getElement("app-update-view-newversion").innerHTML = newversion;
            }
        }).then(async(result) => {
            if(result.isDismissed) return;
            if(result.isConfirmed) {
                sessionStorage.removeItem(Key.deferupdate)
                subLoader(true);
                loader(true);
                message("Updating...");
                localStorage.setItem(Key.appUpdated, 1);
                try {
                    newServiceWorker.postMessage({ action: "skipWaiting" });
                } catch {
                    window.location.reload();
                }
                return
            }
            if (result.isDenied){
                sessionStorage.setItem(Key.deferupdate, 1)
                show(getElement('new-update-action'), false)
                getElement('new-update-action').onclick=_=>{
                    sessionStorage.removeItem(Key.deferupdate)
                    newUpdateDialog(newServiceWorker)
                }
                message("Okay, we won't remind you in this session.");
            }
        })
    } else {
        getElement('new-update-action').onclick=_=>{
            sessionStorage.removeItem(Key.deferupdate)
            newUpdateDialog(newServiceWorker)
        }
        show(getElement('new-update-action'), false)
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
            })
            .catch((err) => {
                console.log("SW:0:", err)
                error('An internal error occurred. We humbly request you to reload this page.')
            });

        if (Number(localStorage.getItem(Key.appUpdated))) {
            success("App updated successfully.");
            localStorage.removeItem(Key.appUpdated);
        }
    } else {
        message("Your browser doesn't support some of our features ☹️. Please update/change your browser for the best experience.");
    }
};

const initializeNotificationState = (reg) => {
    if (!reg.showNotification) {
        error('Showing notifications isn\'t supported ☹️');
        return
    }
    if (Notification.permission === 'denied') {
        alertify.confirm('Notification', "Please allow us to send useful notifications, we won\'t annoy you.",()=>{
            Notification.requestPermission().then((permission)=> { 
                if (permission === "granted") {
                    initializeNotificationState(reg)
                } else {
                    error('You prevented us from showing notifications.');
                }
            });
        },()=>{
            error('You prevented us from showing notifications.');
        })
        return
    }
    if (!'PushManager' in window) {
        error("Push isn't allowed in your browser 🤔");
        return
    }
    subscribe(reg);
}

function urlB64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, '+')
        .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    const outputData = outputArray.map((_, index) => rawData.charCodeAt(index));

    return outputData;
}

const subscribe = async (reg) => {
    const subscription = await reg.pushManager.getSubscription();
    if (subscription) {
        sendSubData(subscription);
        return;
    }
    const options = {
        userVisibleOnly: true,
        applicationServerKey: urlB64ToUint8Array(VAPID_KEY)
    };

    const sub = await reg.pushManager.subscribe(options);
    sendSubData(sub)
};

const sendSubData = async (subscription) => {
    const browser = navigator.userAgent.match(/(firefox|msie|chrome|safari|trident)/ig)[0].toLowerCase();
    const data = {
        status_type: 'subscribe',
        subscription: subscription.toJSON(),
        browser: browser,
        group: "test_group"
    };
    const resp = await postRequest('/webpush/save_information', data, {},{
        credentials: "include"
    })
    console.log(resp)
};

