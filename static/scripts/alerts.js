const loader = (show = true) => {
    if (show) {
        getElements("swal2-container").forEach((e) => (e.style.zIndex = 1060));
        sessionStorage.setItem(KEY.loader, 1);
        window.dispatchEvent(new CustomEvent(KEY.loader));
    } else {
        sessionStorage.removeItem(KEY.loader);
    }
    visibleElement("viewloader", show);
};
const subLoader = (show = true) => {
    if (show) {
        getElements("swal2-container").forEach((e) => (e.style.zIndex = 1060));
        sessionStorage.setItem(KEY.subLoader, 1);
        window.dispatchEvent(new CustomEvent(KEY.subLoader));
    } else {
        sessionStorage.removeItem(KEY.subLoader);
    }
    visibleElement("subloader", show);
};
subLoader(true);

const loaders = (show = true) => {
    loader(show);
    subLoader(show);
};

window.addEventListener(KEY.message_fired, (e) => {
    let queue = [];
    try {
        queue = JSON.parse(sessionStorage.getItem(KEY.message_queue) || "[]");
    } catch {
        queue = [];
    }
    if (queue.length) {
        const title = queue[0].msg;
        if (!sessionStorage.getItem(KEY.message_firing)) {
            sessionStorage.setItem(KEY.message_firing, 1);
            Swal.mixin({
                toast: true,
                position: "bottom-start",
                showConfirmButton: false,
                iconColor: "#000",
                timer: queue[0].timer,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener("mouseenter", Swal.stopTimer);
                    toast.addEventListener("mouseleave", Swal.resumeTimer);
                    getElements("swal2-container").forEach(
                        (e) => (e.style.zIndex = 999999999)
                    );
                    eval(queue[0].onOpen)(toast);
                },
                didClose: (t) => {
                    sessionStorage.removeItem(KEY.message_firing);
                    let queue = [];
                    try {
                        queue = JSON.parse(
                            sessionStorage.getItem(KEY.message_queue) || "[]"
                        );
                    } catch {
                        queue = [];
                    }
                    queue.shift();
                    sessionStorage.setItem(
                        KEY.message_queue,
                        JSON.stringify(queue, (key, value) => {
                            if (typeof value === "function") {
                                return value.toString();
                            } else {
                                return value;
                            }
                        })
                    );
                    if (queue.length > 0) {
                        window.dispatchEvent(
                            new CustomEvent(KEY.message_fired)
                        );
                    }
                },
            }).fire({
                icon: "info",
                title,
            });
        }
    }
});
window.addEventListener(KEY.error_fired, (e) => {
    let queue = [];
    try {
        queue = JSON.parse(sessionStorage.getItem(KEY.error_queue) || "[]");
    } catch {
        queue = [];
    }
    if (queue.length) {
        const title = queue[0].msg;
        if (!sessionStorage.getItem(KEY.error_firing)) {
            sessionStorage.setItem(KEY.error_firing, 1);
            Swal.mixin({
                toast: true,
                position: "bottom-end",
                showConfirmButton: false,
                iconColor: "#000",
                timer: queue[0].timer,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener("mouseenter", Swal.stopTimer);
                    toast.addEventListener("mouseleave", Swal.resumeTimer);
                    getElements("swal2-container").forEach(
                        (e) => (e.style.zIndex = 999999999)
                    );
                },
                didClose: (t) => {
                    sessionStorage.removeItem(KEY.error_firing);
                    let queue = [];
                    try {
                        queue = JSON.parse(
                            sessionStorage.getItem(KEY.error_queue) || "[]"
                        );
                    } catch {
                        queue = [];
                    }
                    queue.shift();
                    sessionStorage.setItem(
                        KEY.error_queue,
                        JSON.stringify(queue, (key, value) => {
                            if (typeof value === "function") {
                                return value.toString();
                            } else {
                                return value;
                            }
                        })
                    );
                    if (queue.length > 0) {
                        window.dispatchEvent(new CustomEvent(KEY.error_fired));
                    }
                },
            }).fire({
                icon: "error",
                title,
            });
        }
    }
});
window.addEventListener(KEY.success_fired, (e) => {
    let queue = [];
    try {
        queue = JSON.parse(sessionStorage.getItem(KEY.success_queue) || "[]");
    } catch {
        queue = [];
    }
    if (queue.length) {
        const title = queue[0].msg;
        if (!sessionStorage.getItem(KEY.success_firing)) {
            sessionStorage.setItem(KEY.success_firing, 1);
            Swal.mixin({
                toast: true,
                position: "top-end",
                showConfirmButton: false,
                iconColor: "#fff",
                timer: queue[0].timer,
                timerProgressBar: true,
                didOpen: (toast) => {
                    toast.addEventListener("mouseenter", Swal.stopTimer);
                    toast.addEventListener("mouseleave", Swal.resumeTimer);
                    getElements("swal2-container").forEach(
                        (e) => (e.style.zIndex = 999999999)
                    );
                },
                didClose: (t) => {
                    sessionStorage.removeItem(KEY.success_firing);
                    let queue = [];
                    try {
                        queue = JSON.parse(
                            sessionStorage.getItem(KEY.success_queue) || "[]"
                        );
                    } catch {
                        queue = [];
                    }
                    queue.shift();
                    sessionStorage.setItem(
                        KEY.success_queue,
                        JSON.stringify(queue, (key, value) => {
                            if (typeof value === "function") {
                                return value.toString();
                            } else {
                                return value;
                            }
                        })
                    );
                    if (queue.length > 0) {
                        window.dispatchEvent(
                            new CustomEvent(KEY.success_fired)
                        );
                    }
                },
            }).fire({
                icon: "success",
                title,
            });
        }
    }
});

const message = (msg = "", onOpen = (toast) => {}) => {
    sessionStorage.removeItem(KEY.error_firing);
    sessionStorage.removeItem(KEY.success_firing);
    sessionStorage.removeItem(KEY.error_queue);
    sessionStorage.removeItem(KEY.success_queue);
    let queue = [];
    try {
        queue = JSON.parse(sessionStorage.getItem(KEY.message_queue) || "[]");
    } catch {
        queue = [];
    }
    if (queue.length && queue[queue.length - 1].msg == msg) {
        return;
    }
    queue.push({
        msg: msg,
        timer: Math.max(msg.split(" ").length * 500, 5000),
        onOpen: onOpen,
    });
    sessionStorage.setItem(
        KEY.message_queue,
        JSON.stringify(queue, (key, value) => {
            if (typeof value === "function") {
                return value.toString();
            } else {
                return value;
            }
        })
    );
    window.dispatchEvent(new CustomEvent(KEY.message_fired));
};

const error = (msg = STRING.default_error_message, force = false) => {
    sessionStorage.removeItem(KEY.message_firing);
    sessionStorage.removeItem(KEY.success_firing);
    sessionStorage.removeItem(KEY.message_queue);
    sessionStorage.removeItem(KEY.success_queue);
    let queue = [];
    try {
        queue = JSON.parse(sessionStorage.getItem(KEY.error_queue) || "[]");
    } catch {
        queue = [];
    }
    if (queue.length && queue[queue.length - 1].msg == msg) {
        return;
    }
    queue.push({
        msg: msg || STRING.default_error_message,
        timer: Math.max(msg.split(" ").length * 500, 5000),
    });
    sessionStorage.setItem(KEY.error_queue, JSON.stringify(queue));
    window.dispatchEvent(new CustomEvent(KEY.error_fired));
};

const success = (msg = STRING.default_success_message) => {
    sessionStorage.removeItem(KEY.message_firing);
    sessionStorage.removeItem(KEY.error_firing);
    sessionStorage.removeItem(KEY.message_queue);
    sessionStorage.removeItem(KEY.error_queue);
    let queue = [];
    try {
        queue = JSON.parse(sessionStorage.getItem(KEY.success_queue) || "[]");
    } catch {
        queue = [];
    }
    if (queue.length && queue[queue.length - 1].msg == msg) {
        return;
    }
    queue.push({
        msg: msg,
        timer: Math.max(msg.split(" ").length * 500, 5000),
    });
    sessionStorage.setItem(KEY.success_queue, JSON.stringify(queue));
    window.dispatchEvent(new CustomEvent(KEY.success_fired));
};

const loaderHTML = (loaderID = "loader") =>
    `<span class="w3-padding-small"><div class="loader" id="${loaderID}"></div></span>`;
const loadErrorHTML = (
    retryID = "retryload"
) => `<div class="w3-center w3-padding">
${Icon("error", "w3-xxxlarge negative-text")}
<h4>${
    STRING.oops_something_went_wrong
}</h4><button class="primary small" id="${retryID}">${Icon("refresh")} ${
    STRING.retry
}</button></div></div>`;

const betaAlert = () => {
    if (
        window.location.host.startsWith("beta.") ||
        window.location.host.startsWith("localhost") ||
        window.location.host.startsWith("127.0.0.1")
    ) {
        Swal.fire({
            title: `This is ${APPNAME}`,
            html: `
            <h5>
            This is not Knotters.<br/>
            ${APPNAME} is the ${NegativeText(
                "unstable"
            )} version of <a target="_blank" href="${window.location.href.replace(
                "//beta.",
                "//"
            )}">Knotters</a>.<br/>
            New features become available here before release at Knotters.
            </h5>
            <h6>
            None of the information from <a target="_blank" href="https://knotters.org">knotters.org</a> will be made available here, including your account info.
            </h6>
            By staying here, you accept that for any of your data loss at Knotters Beta due to any error, you will solely be responsible.
            `,
            confirmButtonText: STRING.take_me_to_appname,
            denyButtonText: STRING.stay_in_appname,
            showCancelButton: false,
            showDenyButton: true,
            focusConfirm: false,
            allowOutsideClick: false,
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = window.location.href.replace(
                    "//beta.",
                    "//"
                );
            } else {
                window.sessionStorage.setItem("beta-alerted", 1);
                message(STRING.remember_using_appname);
            }
        });
    }
};

const connectWithGithub = (next = URLS.ROOT, oncancel = (_) => {}) => {
    Swal.fire({
        title: STRING.gh_id_required,
        html: `<div class="w3-row w3-padding">
        <h4>${STRING.must_link_gh_account}</h4>
        </div>`,
        imageUrl: setUrlParams(STATIC_URL, "graphics/thirdparty/github.webp"),
        confirmButtonText: `${Icon("open_in_new")} ${STRING.link_gh_account}`,
        cancelButtonText: STRING.leave_it,
        showCancelButton: true,
    }).then((res) => {
        if (res.isConfirmed) {
            return (window.location.href = setUrlQueries(
                `${URLS.Auth.GITHUB}login/`,
                {
                    process: "connect",
                    next: setUrlQueries(URLS.REDIRECTOR, { n: next }),
                }
            ));
        } else {
            oncancel();
        }
    });
};

const troubleShootingInfo = () => {
    Swal.fire({
        title: STRING.troubleshooting,
        html: `
            <div class="w3-row w3-left">
            <h5>If you are facing problems during normal usage of ${APPNAME}, then any or all of the following steps might help you out.</h5>
            <br/>
            <strong class="text-medium">
            <a href="https://www.google.com/search?q=clear+browser+cache" target="_blank" rel="noreferrer">Clear your browser's cache</a>
            <br/><br/>
            <a href="https://www.google.com/search?q=how+to+clear+specific+site+data" target="_blank" rel="noreferrer">Clear site data</a> from your browser's settings
            ${AUTHENTICATED ? "<br/>(this will log you out)" : ""}
            <br/><br/>
            <a href="https://www.google.com/search?q=hard+reload+site" target="_blank" rel="noreferrer">Force reload current page</a>
            </span>
            </div>
        `,
        confirmButtonText: STRING.problem_solved,
        denyButtonText: STRING.problem_unsolved,
        showCancelButton: false,
        showDenyButton: true,
        preConfirm: () => {},
    }).then((res) => {
        if (res.isConfirmed) {
            message(STRING.glad_to_help);
        } else if (res.isDenied) {
            window.scrollTo(0, document.body.scrollHeight);
            message(
                STRING.sorry_couldnt_help + " " + STRING.click_to_report,
                (toast) => {
                    toast.onclick = (_) => reportFeedbackView();
                }
            );
        }
    });
};

const blockUserView = ({ userID = "", username = "", userDP = null }) => {
    Swal.fire({
        title: `Block ${username}?`,
        imageUrl: userDP,
        imageWidth: 100,
        html: `<h6>${STRING.you_sure_to} ${NegativeText(
            `${STRING.block} ${username}`
        )}?
        <br/>You both will be invisible to each other on ${APPNAME},<br/>including all associated activities.
        <br/>${STRING.you_can_unblock_from}
        </h6>`,
        showDenyButton: true,
        confirmButtonText: STRING.no_wait,
        denyButtonText: STRING.yes_block,
    }).then(async (res) => {
        if (res.isDenied) {
            loader();
            message(STRING.blocking);
            const data = await postRequest(
                URLS.People ? URLS.People.BLOCK_USER : URLS.BLOCK_USER,
                {
                    userID,
                }
            );
            if (!data) return loader(false);
            if (data.code === code.OK) {
                futuremessage(`${STRING.blocked} ${username}.`);
                return window.location.replace(ROOT);
            }
            loader(false);
            error(data.error);
        }
    });
};

const installWebAppInstructions = (show = true) => {
    const dial = Swal.mixin({
        title: "Web App Support",
        html: `
        <div class="w3-row w3-padding">
            <h5>
            ${
                isStandaloneMode()
                    ? `You may have already installed ${APPNAME} on your device.`
                    : `${
                          canInstallPWA()
                              ? `You might be able to install ${APPNAME} as a web app on your device`
                              : `You may not be able to install ${APPNAME} on your device via your current browser.`
                      }`
            }
            </h5>
            <div class="w3-row text-medium">
            Install ${APPNAME} as a web app by any one of the following ways.
            </div>
            <br/>
            <div class="w3-row ">
            <div class="w3-col w3-half w3-padding-small">
            <img src="${setUrlParams(
                STATIC_URL,
                "graphics/info/install-pwa-chrome-win.webp"
            )}" title="Chrome on Windows" alt="Chrome on Windows" class="wide preview-type-image w3-card w3-round"  />
                </div>
                <div class="w3-col w3-half w3-padding-small">
                <img src="${setUrlParams(
                    STATIC_URL,
                    "graphics/info/install-pwa-chrome-android.webp"
                )}" title="Chrome on Android" alt="Chrome on Android" class="wide preview-type-image w3-card w3-round" />
                </div>
            </div>
            <br/>
            <div class="w3-row">
                The images may not exactly depict your device's config, but could be relevant.
            </div>
        </div>
        `,
        confirmButtonText: STRING.got_it,
        showCancelButton: false,
        showDenyButton: false,
        didOpen: () => {
            loadGlobalEventListeners();
        },
        preConfirm: () => {},
    });
    if (show) dial.fire();
};

const previewImageDialog = (src, alt = "", title = "") => {
    if (!src) return;
    getElement("image-previewer").style.display = "flex";
    getElement("image-previewer").addEventListener("click", (e) => {
        if (e.target.id !== "preivew-image-src") {
            e.target.style.display = "none";
        }
    });
    getElement("preivew-image-src").src = src;
    getElement("preivew-image-src").alt = alt;
    getElement("preivew-image-src").title = title;
    firstTimeMessage(KEY.previewImageInfo, STRING.close_preview_img_help);
};

const futureMessage = (message = "") => {
    localStorage.setItem(Key.futureMessage, message);
};

const futuremessage = futureMessage;

const firstTimeMessage = (key, _message = "") => {
    if (localStorage.getItem(`first-intro-${key}`) != 1) {
        message(_message);
        localStorage.setItem(`first-intro-${key}`, 1);
    }
};

const _reauthenticate = async (
    afterSuccess = (_) => {},
    afterFailure = (_) => {}
) => {
    if (!authenticated) return afterFailure();
    loader();
    const vdata = await postRequest2({
        path: URLS.Auth.VERIFY_REAUTH_METHOD,
        retainCache: true,
    });
    loader(false);
    if (!vdata || vdata.code != CODE.OK) {
        return error(vdata.error);
    }
    let authinput = "";
    if (vdata.methods.length) {
        vdata.methods.forEach((method)=>{
            if(method == 'password'){
                authinput += `<input class="reauth-input" name="${method}" type="password" id="reauth-input-${method}" placeholder="${APPNAME} ${STRING.password}" />`;
            }
            if(method == 'totp'){
                authinput += `<br/>Or<br/><input class="reauth-input" name="${method}" type="text" id="reauth-input-${method}" placeholder="${STRING.two_fa_token_or_backup}" />`;
            }
        })
    } else {
        return afterSuccess();
    }
    Swal.fire({
        title: "Verify yourself",
        html: `
        <div class="w3-row w3-padding">
        ${Icon('lock', 'w3-jumbo')}
        <h6>
        ${STRING.reauth_to_continue}
        </h6>
        ${authinput}
        </div>
        `,
        confirmButtonText: STRING.continue,
        showCancelButton: false,
        showDenyButton: true,
        denyButtonText: STRING.cancel,
        preConfirm: () => {
            if(!getElements("reauth-input").some((input)=>input.value)){
                error(STRING.password_or_2fa_required);
                return false
            }
            let value = {}
            getElements("reauth-input").forEach((input)=>(value[input.name]=input.value));
            return value
        },
    }).then(async (res) => {
        if (res.isConfirmed) {
            loader();
            const data = await postRequest2({
                path: URLS.Auth.VERIFY_REAUTH,
                data: {
                    ...res.value,
                },
            });
            loader(false);
            if (data && data.code === code.OK) {
                return afterSuccess();
            }
            error(data.error);
            afterFailure();
        }
    });
};

const clearToastQueue = () => {
    sessionStorage.removeItem(KEY.message_firing);
    sessionStorage.removeItem(KEY.error_firing);
    sessionStorage.removeItem(KEY.success_firing);
    sessionStorage.removeItem(KEY.message_queue);
    sessionStorage.removeItem(KEY.error_queue);
    sessionStorage.removeItem(KEY.success_queue);
    sessionStorage.removeItem(KEY.message_fired);
    sessionStorage.removeItem(KEY.error_fired);
    sessionStorage.removeItem(KEY.success_fired);
};

const contactRequestDialog = async () => {
    const data = await getRequest2({ path: URLS.Management.CONTACT_REQUEST_CATEGORIES });
    let options = `<option class="text-medium" value="">Click to choose</option>`;
    data.categories.forEach((rep) => {
        options += `<option class="text-medium" value='${rep.id}'>${rep.name}</option>`;
    });
    await Swal.fire({
        title: STRING.contact_us,
        html: `
        <div class="w3-row w3-center">
            <input class="wide" type="text" autocomplete="name" id="contact-name" placeholder="${STRING.your_name}" /><br/><br/>
            <input class="wide" type="email" autocomplete="email" id="contact-email" placeholder="${STRING.your_email_addr}" /><br/><br/>
            <br/><span>Your reason to contact us</span><br/>
            <select class="wide pallete-slab" id="contact-category-id">${options}</select>
            <textarea class="wide" rows="5" autocomplete="organization" id="contact-message" placeholder="${STRING.contact_message}" ></textarea>
            <strong class="negative-text" id="contact-error"></strong>
        </div>
        `,
        showCancelButton: true,
        showConfirmButton: true,
        confirmButtonText: STRING.send,
        cancelButtonText: STRING.cancel,
        preConfirm: () => {
            const error = getElement("contact-error");
            
            const senderName = String(getElement("contact-name").value).trim();
            if (!senderName) {
                error.innerHTML = STRING.your_name_required;
                return false;
            }
            const senderEmail = String(getElement("contact-email").value).trim();
            if (!senderEmail||!isValidEmail(senderEmail)) {
                error.innerHTML = STRING.your_email_required;
                return false;
            }
            const contactCategoryID = String(getElement("contact-category-id").value).trim();
            if (!contactCategoryID) {
                error.innerHTML = STRING.contact_reason_required;
                return false;
            }
            const senderMessage = String(getElement("contact-message").value).trim();
            if (!senderMessage) {
                error.innerHTML = STRING.contact_message_required;
                return false;
            }
            return {contactCategoryID, senderName, senderEmail, senderMessage}
        },
        preDeny: () => {
            message(STRING.dont_hesitate_contact_us);
        },
    }).then(async (result) => {
        if (result.isConfirmed && result.value.senderEmail){
            const done = await postRequest2({
                path: URLS.Management.CONTACT_SUBM,
                data: result.value,
                retainCache: true,
            })
            if(done&&done.code==CODE.OK){
                return message(STRING.contact_request_received)
            }
            error(data.error)
        }
    })
}