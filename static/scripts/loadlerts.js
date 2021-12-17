const loader = (show = true) => {
    if (show) {
        getElements("swal2-container").forEach((e) => (e.style.zIndex = 1060));
    }
    visibleElement("viewloader", show);
};
const subLoader = (show = true) => {
    if (show) {
        getElements("swal2-container").forEach((e) => (e.style.zIndex = 1060));
    }
    visibleElement("subloader", show);
};
subLoader(true);

const loaders = (show = true) => {
    loader(show);
    subLoader(show);
};

const message = (msg = "") => {
    Swal.mixin({
        toast: true,
        position: "bottom-start",
        showConfirmButton: false,
        iconColor: "#000",
        timer: Math.max(msg.split(" ").length * 400, 3000),
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener("mouseenter", Swal.stopTimer);
            toast.addEventListener("mouseleave", Swal.resumeTimer);
            getElements("swal2-container").forEach(
                (e) => (e.style.zIndex = 999999999)
            );
        },
    }).fire({
        icon: "info",
        title: msg,
    });
};

const error = (msg = STRING.default_error_message, force = false) => {
    if (msg !== STRING.default_error_message || force) {
        Swal.mixin({
            toast: true,
            position: "bottom-end",
            showConfirmButton: false,
            iconColor: "#000",
            timer: Math.max(msg.split(" ").length * 400, 3000),
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener("mouseenter", Swal.stopTimer);
                toast.addEventListener("mouseleave", Swal.resumeTimer);
                getElements("swal2-container").forEach(
                    (e) => (e.style.zIndex = 999999999)
                );
            },
        }).fire({
            icon: "error",
            title: msg || STRING.default_error_message,
        });
    }
};

const success = (msg = "Success") => {
    Swal.mixin({
        toast: true,
        position: "top-end",
        showConfirmButton: false,
        iconColor: "#fff",
        timer: Math.max(msg.split(" ").length * 400, 3000),
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener("mouseenter", Swal.stopTimer);
            toast.addEventListener("mouseleave", Swal.resumeTimer);
            getElements("swal2-container").forEach(
                (e) => (e.style.zIndex = 999999999)
            );
        },
    }).fire({
        icon: "success",
        title: msg,
    });
};

const loaderHTML = (loaderID = "loader") =>
    `<span class="w3-padding-small"><div class="loader" id="${loaderID}"></div></span>`;
const loadErrorHTML = (
    retryID = "retryload"
) => `<div class="w3-center w3-padding-32">
<i class="negative-text material-icons w3-jumbo">error</i>
<h3>Oops. Something wrong here?</h3><button class="primary" id="${retryID}">Retry</button></div></div>`;
