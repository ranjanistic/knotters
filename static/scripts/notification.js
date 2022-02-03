const togglePushSubscription = async ({
    statusType,
    subscription,
    group = null,
    callback = (data) => {},
    browser = _BROWSER,
}) => {
    const done = await postRequest2({
        path: "/webpush/save_information",
        data: {
            status_type: statusType,
            subscription: subscription.toJSON(),
            browser,
            group,
        },
        retainCache: true,
        options: {
            credentials: "include",
        },
        silent: true
    });
    callback(done);
};

const subscribeToPush = async (
    group = null,
    title = APPNAME,
    silent = false,
    done = async (subscription, err = null) => {}
) => {
    const reg = await navigator.serviceWorker.getRegistration();
    reg.pushManager.getSubscription().then((subscription) => {
        if (subscription) {
            togglePushSubscription({
                statusType: "subscribe",
                subscription,
                group,
                callback: (response) => {
                    if (response) {
                        if(!silent){
                            message(
                                STRING.subscribed_to_notif_of +
                                    " " + title
                            );
                        }
                        done(subscription);
                    }
                    return response;
                },
            });
        } else {
            reg.pushManager
                .subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlB64ToUint8Array(VAPID_KEY),
                })
                .then((subscription) => {
                    togglePushSubscription({
                        statusType: "subscribe",
                        subscription,
                        group,
                        callback: (response) => {
                            if (response) {
                                if(!silent){
                                    message(
                                        STRING.subscribed_to_notif_of +
                                            " " + title
                                    );
                                }
                                done(subscription, null);
                            } else {
                                done(response)
                            }
                            return response;
                        },
                    });
                })
                .catch((error) => {
                    console.log("Subscription error.", error);
                    done(false, error);
                    return false;
                });
        }
    });
};

const urlB64ToUint8Array = (base64String) => {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding)
        .replace(/\-/g, "+")
        .replace(/_/g, "/");

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
};

const unsubscribeFromPush = async (
    group = null,
    title = null,
    silent = false,
    done = async(subscription, err = null) => {}
) => {
    const reg = await navigator.serviceWorker.getRegistration();
    reg.pushManager.getSubscription().then(function (subscription) {
        if (!subscription) {
            done(true, null);
            return true;
        }
        return togglePushSubscription({
            statusType: "unsubscribe",
            subscription,
            group,
            callback: (resp) => {
                if (resp) {
                    return subscription
                        .unsubscribe()
                        .then((successful) => {
                            if(successful){
                                if(!silent){
                                    message(
                                        STRING.unsubscribed_from_notif_of +
                                            " " + title
                                    );
                                }
                                done(subscription, null)
                            } else {
                                done(successful)
                            }
                            return successful;
                        })
                        .catch((error) => {
                            console.log("Unsubscription error.", error);
                            done(false,error)
                            return false;
                        });
                }
            },
        });
    });
};
