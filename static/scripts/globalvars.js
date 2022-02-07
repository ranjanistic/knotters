const KEY = {
    appUpdated: "app-updated",
    navigated: "navigated",
    futureMessage: "future-message",
    deferupdate: "deferupdate",
    previewImageInfo: "preview-image-info",
    current_theme: "theme",
    message_firing: "message_firing",
    error_firing: "error_firing",
    success_firing: "success_firing",
    message_queue: "message-queue",
    error_queue: "error-queue",
    success_queue: "success-queue",
    message_fired: "message-fired",
    error_fired: "error-fired",
    success_fired: "success-fired",
    loader: "global-loader",
    subLoader: "sub-loader",
};
const Key = KEY;

const CODE = {
    OK: "OK",
    NO: "NO",
    LEFT: "left",
    RIGHT: "right",
};
const code = CODE;

let __appInstallPromptEvent = null;
const _BROWSER = navigator.userAgent
    .match(/(firefox|msie|chrome|safari|trident)/gi)[0]
    .toLowerCase();

Swal = Swal.mixin({ 
    scrollbarPadding: false,
    confirmButtonText: STRING.okay,
    didOpen:(d)=>{
        loadGlobalEventListeners();
        loadGlobalEditors();
        loadCarousels({});
        loadBrowserSwiper();
        if(d.getAttribute("role")=='dialog'){
            clearToastQueue();
        }
    }
});
