const newUpdateDialog = (newServiceWorker) => {
    if(sessionStorage.getItem(Key.deferupdate)!=1){
        alertify
            .confirm(
                `Update available`,
                `
                <img src="${ICON}" width="50" />
                <h4>A new version of ${APPNAME} is available, with new features & performance improvements.<br/><br/>Shall we update?<h4>
                <h6 class="dead-text">Updates are important. It will take a few seconds, depending upon your network strength.</h6>`,
                () => {
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
                },
                () => {
                    sessionStorage.setItem(Key.deferupdate, 1)
                    show(getElement('new-update-action'), false)
                    getElement('new-update-action').onclick=_=>{
                        sessionStorage.removeItem(Key.deferupdate)
                        newUpdateDialog(newServiceWorker)
                    }
                    message("Okay, we won't remind you in this session.");
                }
            )
            .set("labels", { ok: `Yes, update now`, cancel: "Not now" })
            .set('transition','flipx')
            .set("closable", false)
            .set("modal", true);
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
                // initializeNotificationState(reg)
            })
            .catch((err) => console.log("Service worker not registered", err));

        if (Number(localStorage.getItem(Key.appUpdated))) {
            success("App updated successfully.");
            localStorage.removeItem(Key.appUpdated);
        }
    }
};

const initializeNotificationState = (reg) => {
    if (!reg.showNotification) {
        error('Showing notifications isn\'t supported ☹️😢');
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

