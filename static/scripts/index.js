"use strict";

const Key = {
    appUpdated: "app-updated",
    navigated: "navigated",
    futureMessage: "future-message",
    deferupdate: "deferupdate",
};

const code = {
    OK: "OK",
    NO: "NO",
    LEFT: "left",
    RIGHT: "right",
};

const logOut = async (
    afterLogout = (_) => {
        window.location.replace(URLS.ROOT);
    }
) => {
    const done = await postRequest(URLS.Auth.LOGOUT);
    if (!done.location) return error("Failed to logout");
    message("Logged out successfully");
    afterLogout();
};

const getElement = (id) => document.getElementById(id);

const getElements = (classname) =>
    Array.from(document.getElementsByClassName(classname));

const getElementsByTag = (tagname) =>
    Array.from(document.getElementsByTagName(tagname));

const hide = (element, display = true) => {
    element.hidden = true;
    if (display) element.style.display = "none";
};
const show = (element, display = true) => {
    element.hidden = false;
    if (display) element.style.display = "block";
};

const hideElement = (id) => visibleElement(id, false);

const showElement = (id) => visibleElement(id, true);

const visibleElement = (id, show = true) => {
    getElement(id).hidden = show ? false : true;
    getElement(id).style.display = show ? "block" : "none";
};

const visible = (element, show = true) => visibleElement(element.id, show);

const loader = (show = true) => visibleElement("viewloader", show);
const subLoader = (show = true) => visibleElement("subloader", show);
subLoader(true);
const loaders = (show = true) => {
    loader(show);
    subLoader(show);
};

const openSpinner = (id = "loader") => showElement(id);

const hideSpinner = (id = "loader") => {
    try {
        hideElement(id);
    } catch {}
};

const csrfHiddenInput = (token) =>
    `<input type="hidden" name="csrfmiddlewaretoken" value="${token}"></input>`;

const miniWindow = (url, name = APPNAME) =>
    window.open(
        setUrlQueries(url, { miniwin: 1 }),
        name,
        "height=650,width=450"
    );

const newTab = (url) => {
    window.open(setUrlQueries(url, { miniwin: 1 }));
};

const message = (msg = "") => {
    alertify.set("notifier", "position", "top-left");
    alertify.message(msg);
};

const error = (msg = "Something went wrong, try that again?") => {
    alertify.set("notifier", "position", "bottom-right");
    alertify.error(msg);
};

const success = (msg = "Success") => {
    alertify.set("notifier", "position", "top-right");
    alertify.success(msg);
};

const loaderHTML = (loaderID = "loader") =>
    `<span class="w3-padding-small"><div class="loader" id="${loaderID}"></div></span>`;
const loadErrorHTML = (
    retryID = "retryload"
) => `<div class="w3-center w3-padding-32">
<i class="negative-text material-icons w3-jumbo">error</i>
<h3>Oops. Something wrong here?</h3><button class="primary" id="${retryID}">Retry</button></div></div>`;

const loadBrowserSwiper = (_) => {
    loadCarousels({
        container: "swiper-browser",
        freeMode: true,
        breakpoints: {
            1024: {
                slidesPerView: 4,
                spaceBetween: 15,
            },
            768: {
                slidesPerView: 3,
                spaceBetween: 10,
            },
            920: {
                slidesPerView: 4,
                spaceBetween: 10,
            },
            640: {
                slidesPerView: 4,
                spaceBetween: 10,
            },
        },
    });
};

const loadBrowsers = () => {
    Promise.all(
        getElements("browser-view").map(async (view) => {
            let method = async () => {
                setHtmlContent(view, loaderHTML(`${view.id}-loader`));
                const data = await getRequest(
                    setUrlParams(URLS.BROWSER, view.getAttribute("data-type"))
                );
                if (!data) {
                    setHtmlContent(
                        view,
                        loadErrorHTML(`${view.id}-load-retry`)
                    );
                    getElement(`${view.id}-load-retry`).onclick = (_) =>
                        method();
                    return;
                }
                setHtmlContent(view, data, loadBrowserSwiper);
                loadBrowserSwiper();
            };
            await method();
        })
    )
        .then(() => {
            loadBrowserSwiper();
        })
        .catch((e) => {
            console.warn(e);
        });
};

const setHtmlContent = (element, content = "", afterset = () => {}) => {
    element.innerHTML = content;
    loadGlobalEventListeners();
    loadGlobalEditors();
    loadCarousels({});
    loadBrowserSwiper();
    afterset();
};

const setUrlParams = (path, ...params) => {
    params.forEach((param) => {
        path = String(path).replace("*", param);
    });
    return path;
};

const setUrlQueries = (path, query = {}) => {
    path = String(path);
    Object.keys(query).forEach((key) => {
        path = `${path}${path.includes("?") ? "&" : "?"}${key}=${query[key]}`;
    });
    return path;
};

const loadGlobalEventListeners = () => {
    getElements("first-time-view").forEach((view) => {
        if (localStorage.getItem(`first-intro-${view.id}`) == 1) {
            hide(view);
        } else {
            view.innerHTML = view.getAttribute("data-html");
            getElement(`close-${view.id}`).addEventListener("click", () => {
                localStorage.setItem(`first-intro-${view.id}`, 1);
                message(
                    "Press Alt+R for introduction, or visit The Landing Page"
                );
                hide(view);
            });
        }
    });
    getElementsByTag("form").forEach((form) => {
        form.addEventListener("submit", (e) => {
            if (form.classList.contains("no-auto")) {
                return e.preventDefault();
            }
            subLoader(true);
        });
    });
    getElementsByTag("a").forEach((a) => {
        if (
            a.getAttribute("href") &&
            !a.getAttribute("href").startsWith("#") &&
            !a.getAttribute("target") &&
            a.getAttribute("download") === null
        ) {
            a.addEventListener("click", (e) => {
                subLoader(true);
            });
        }
    });
    getElements("href").forEach((href) => {
        href.addEventListener("click", (e) => {
            subLoader(true);
            window.location.href = href.getAttribute("data-href");
        });
    });
    getElementsByTag("button").forEach((button) => {
        if (button.getAttribute("data-icon")) {
            if (!button.innerHTML.includes("material-icons")) {
                button.innerHTML = `${Icon(button.getAttribute("data-icon"))}${
                    button.innerHTML
                }`;
            }
        }
    });
    getElementsByTag("i").forEach((icon) => {
        icon.classList.add("material-icons");
    });

    getElements("preview-type-image").forEach((image) => {
        image.classList.add("pointer");
        image.addEventListener("click", (e) => {
            previewImageDialog(e.target.src);
        });
    });

    getElements("click-to-copy").forEach((elem) => {
        elem.classList.add("pointer");
        elem.addEventListener("click", (e) => {
            copyToClipboard(
                e.target.getAttribute("data-copy") || e.target.innerHTML
            );
        });
    });
    getElements("previous-action-button").forEach((elem) => {
        elem.addEventListener("click", () => {
            window.close();
        });
    });
    getElements("recaptcha-protected-form-action").forEach((action) => {
        action.onclick = (e) => {
            e.preventDefault();
            if (
                !getElements("required-field").every((field) => {
                    if (!String(field.value).trim()) {
                        error(field.placeholder + " required");
                        return false;
                    }
                    return true;
                })
            )
                return;
            subLoader(true);
            _processReCaptcha((stopLoaders) => {
                e.target.form.submit();
                return;
            });
        };
    });
    getElements("close-global-alert").forEach((closer) => {
        if (localStorage.getItem(`hidden-alert-${closer.id}`)) {
            hide(getElement(`view-${closer.id}`));
        }
        closer.addEventListener("click", (e) => {
            hide(getElement(`view-${closer.id}`));
            localStorage.setItem(`hidden-alert-${closer.id}`, closer.id);
        });
    });

    getElements("navigator-share-action").forEach((share)=>{
        share.addEventListener("click", ()=>{
            shareLinkAction(share.getAttribute("data-title"), share.getAttribute("data-text"), share.getAttribute("data-url"));
        })
    })
};

const copyToClipboard = (text) => {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text);
        success("Copied to clipboard");
    } else {
        error("Unable to copy!");
    }
};

const _processReCaptcha = (
    onSuccess = (stopLoaders) => {},
    onFailure = (e) => {
        error("Something went wrong, try that again?");
    }
) => {
    try {
        grecaptcha.ready(function () {
            try {
                grecaptcha
                    .execute(RECAPTCHA_KEY, { action: "submit" })
                    .then(async (token) => {
                        loader(true);
                        const data = await postRequest(URLS.VERIFY_CAPTCHA, {
                            "g-recaptcha-response": token,
                        });
                        if (!data) {
                            subLoader(false);
                            loader(false);
                            return;
                        }
                        if (data.code === code.OK) {
                            onSuccess(() => {
                                loader(false);
                                subLoader(false);
                            });
                        } else {
                            onFailure(data);
                            subLoader(false);
                            loader(false);
                        }
                    })
                    .catch((e) => {
                        onFailure(e);
                        subLoader(false);
                        loader(false);
                    });
            } catch (e) {
                onFailure(e);
                subLoader(false);
                loader(false);
            }
        });
    } catch {
        onSuccess(() => {
            loader(false);
            subLoader(false);
        });
    }
};

const Icon = (name, classnames = "") =>
    `<i class="material-icons ${classnames}">${name}</i>`;

const loadCarousels = ({
    container = "swiper-container",
    loop = false,
    grabCursor = true,
    spaceBetween = 2,
    breakpoints = {
        640: {
            slidesPerView: 2,
            spaceBetween: 0,
        },
        768: {
            slidesPerView: 2,
            spaceBetween: 0,
        },
        1024: {
            slidesPerView: 3,
            spaceBetween: 0,
        },
    },
}) => {
    if (getElements(container).length) {
        return new Swiper(`.${container}`, {
            loop,
            grabCursor,
            spaceBetween,
            breakpoints,
            freeMode: true,
        });
    }
    return null;
};

const initializeTabsView = ({
    onEachTab = async (tab) => {},
    uniqueID,
    onShowTab = async (tab) => {},
    tabsClass = "nav-tab",
    activeTabClass = "positive",
    inactiveTabClass = "primary",
    viewID = "tabview",
    spinnerID = "loader",
    selected = 0,
    setDefaultViews = true,
    tabindex = false,
}) => {
    const tabs = getElements(tabsClass);
    let tabview = null;
    spinnerID = spinnerID + uniqueID;
    try {
        if (viewID) {
            tabview = getElement(viewID);
        }
    } catch {}

    const showTabLoading = () => {
        if (tabview) {
            setHtmlContent(tabview, loaderHTML(spinnerID));
            openSpinner(spinnerID);
        }
    };

    const showTabError = (tab) => {
        if (tabview) {
            setHtmlContent(tabview, loadErrorHTML(`${uniqueID}retry`));
            getElement(`${uniqueID}retry`).onclick = (_) => tab.click();
        }
    };

    const showTabContent = (tab, content) => {
        if (tabview) {
            setHtmlContent(tabview, content);
        }
        onShowTab(tab);
    };

    tabs.forEach(async (tab, t) => {
        tab.onclick = async () => {
            if (setDefaultViews) {
                showTabLoading();
            }
            sessionStorage.setItem(uniqueID, t);
            const onclicks = Array(tabs.length);
            tabs.forEach((tab1, t1) => {
                onclicks[t1] = tab1.onclick;
                tab1.onclick = (_) => {};
                if (t1 === t) {
                    activeTabClass
                        .split(" ")
                        .forEach((active) => tab1.classList.add(active));
                    inactiveTabClass
                        .split(" ")
                        .forEach((inactive) => tab1.classList.remove(inactive));
                } else {
                    tab1.style.opacity = 0;
                    activeTabClass
                        .split(" ")
                        .forEach((active) => tab1.classList.remove(active));
                    inactiveTabClass
                        .split(" ")
                        .forEach((inactive) => tab1.classList.add(inactive));
                }
            });
            const response = await onEachTab(tab);
            if (tabview && setDefaultViews) hideSpinner(spinnerID);
            tabs.forEach((tab1, t1) => {
                if (t1 !== t) {
                    tab1.style.opacity = 1;
                }
                tab1.onclick = onclicks[t1];
            });
            return response
                ? showTabContent(tab, response)
                : setDefaultViews
                ? showTabError(tab)
                : "";
        };
    });
    if (tabs.length) {
        if (tabindex === false) {
            try {
                tabs[Number(sessionStorage.getItem(uniqueID)) || 0].click();
            } catch (e) {
                tabs[selected].click();
            }
        } else {
            if (tabindex < tabs.length) {
                tabs[tabindex].click();
            } else {
                tabs[tabs.length - 1].click();
            }
        }
    }
    return tabs;
};

const initializeMultiSelector = ({
    candidateClass = "multi-select-candidate",
    selectedClass = "positive",
    deselectedClass = "primary",
    onSelect = async (candidate) => true,
    onDeselect = async (candidate) => true,
    uniqueID = String(Math.random()),
}) => {
    const candidates = getElements(candidateClass);
    let selectedlist = [],
        deselectedList = candidates;
    candidates.forEach((candidate) => {
        candidate.addEventListener("click", () => {
            if (deselectedList.includes(candidate)) {
                if (onSelect(candidate)) {
                    deselectedList = deselectedList.filter(
                        (cand) => cand != candidate
                    );
                    selectedlist.push(candidate);
                    deselectedClass.split(" ").forEach((cl) => {
                        if (cl) candidate.classList.remove(cl);
                    });
                    selectedClass.split(" ").forEach((cl) => {
                        if (cl) candidate.classList.add(cl);
                    });
                }
            } else if (selectedlist.includes(candidate)) {
                if (onDeselect(candidate)) {
                    selectedlist = selectedlist.filter(
                        (cand) => cand != candidate
                    );
                    deselectedList.push(candidate);
                    deselectedClass.split(" ").forEach((cl) => {
                        if (cl) candidate.classList.add(cl);
                    });
                    selectedClass.split(" ").forEach((cl) => {
                        if (cl) candidate.classList.remove(cl);
                    });
                }
            }
        });
    });
    return candidates;
};

const postRequest = async (path, data = {}) => {
    const body = { ...data };
    try {
        subLoader();
        const response = await window.fetch(path, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrfmiddlewaretoken,
                "X-KNOT-REQ-SCRIPT": true,
            },
            body: JSON.stringify(body),
        });
        const data = await response.json();
        subLoader(false);
        return data;
    } catch (e) {
        error("Something went wrong, try that again?");
        subLoader(false);
        return false;
    }
};

const getRequest = async (url, query = {}) => {
    try {
        subLoader();
        const response = await window.fetch(setUrlQueries(url, query), {
            method: "GET",
            headers: {
                "X-CSRFToken": csrfmiddlewaretoken,
                "X-KNOT-REQ-SCRIPT": true,
            },
        });
        const data = await response.text();
        subLoader(false);
        return data;
    } catch (e) {
        subLoader(false);
        return false;
    }
};

const loadGlobalEditors = (onSave = (done) => done(), onDiscard) => {
    getElements("edit-action").forEach((edit) => {
        const target = edit.getAttribute("data-edittarget"),
            viewer = getElement(`view-${target}`),
            editor = getElement(`edit-${target}`),
            discard = getElement(`discard-edit-${target}`),
            save = getElement(`save-edit-${target}`);
        hide(editor);
        show(viewer);
        save.classList.add("positive", "small");
        save.type = "submit";
        discard.classList.add("negative", "small");
        discard.type = "button";
        edit.onclick = (_) => {
            hide(viewer);
            show(editor);
            discard.onclick = (_) => {
                if (onDiscard) {
                    onDiscard(() => {
                        hide(editor);
                        show(viewer);
                    });
                } else {
                    hide(editor);
                    show(viewer);
                }
            };
            save.onclick = (_) => {
                onSave(() => {
                    hide(editor);
                    show(viewer);
                });
            };
        };
    });
};

const shareLinkAction = (title, text, url, afterShared = (_) => {}) => {
    if (!url.startsWith(SITE)) {
        if (url.startsWith("/")) {
            url = SITE + url;
        } else {
            url = SITE + "/" + url;
        }
    }
    if (!title.endsWith("\n")) {
        title = title + "\n";
    }
    if (!text.endsWith("\n")) {
        text = text + "\n";
    }
    if (navigator.share) {
        subLoader();
        navigator
            .share({ title, text, url })
            .then(() => {
                subLoader(false);
                afterShared();
            })
            .catch((e) => {
                subLoader(false);
            });
    } else {
        error("Sharing not available on your system.");
        copyToClipboard(url);
    }
};

const handleCropImageUpload = (
    event,
    dataOutElemID,
    previewImgID,
    onCropped = (croppedB64) => {},
    ratio = 1 / 1
) => {
    const file = Array.from(event.target.files)[0];
    if (file) loader();
    const reader = new FileReader();
    reader.onload = (_) => {
        const base64String = reader.result;

        alertify
            .confirm(
                "Crop Image",
                `<div class="w3-row w3-center">
					<img src="${base64String}" style="max-width:100%" id="tempprofileimageoutput" />
				</div>`,
                () => {
                    try {
                        const croppedB64 = cropImage
                            .getCroppedCanvas()
                            .toDataURL("image/png");
                        if (String(croppedB64).length / 1024 / 1024 >= 10) {
                            return error(
                                "Image too large. Preferred size < 10 MB"
                            );
                        }
                        getElement(dataOutElemID).value = croppedB64;
                        getElement(previewImgID).src = croppedB64;
                        onCropped(croppedB64);
                    } catch (e) {
                        console.debug(e);
                        error(
                            `Something went wrong. <br/><button class="small primary" onclick="window.location.reload();">Reload</button>`
                        );
                    }
                },
                () => {}
            )
            .set("closable", false)
            .set("labels", {
                ok: "Confirm",
                cancel: "Cancel",
            });
        const cropImage = new Cropper(getElement("tempprofileimageoutput"), {
            ...(ratio !== true ? { aspectRatio: ratio } : {}),
            viewMode: 1,
            responsive: true,
            center: true,
        });
        loader(false);
    };
    if (file) {
        reader.readAsDataURL(file);
    }
};

const b64toBlob = (b64Data, contentType = "", sliceSize = 512) => {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];

    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
        const slice = byteCharacters.slice(offset, offset + sliceSize);

        const byteNumbers = new Array(slice.length);
        for (let i = 0; i < slice.length; i++) {
            byteNumbers[i] = slice.charCodeAt(i);
        }

        const byteArray = new Uint8Array(byteNumbers);
        byteArrays.push(byteArray);
    }

    const blob = new Blob(byteArrays, { type: contentType });
    return blob;
};

const fileToBase64 = async (file) => {
    try{
        return await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result);
            reader.onerror = error => reject(error);
        });
    } catch(e) {
        error('Failed to process file')
        return null
    }
}

const handleFileUpload = (fileoutputs=[], title='Upload') => {
    let fileinputs = '';
    let inputIDs = []
    fileoutputs.forEach((f)=>{
        let id = `handle-file-input-${f.id}`
        fileinputs+=`<input hidden id="${id}" type="file" />`
        inputIDs.push(id)
    })
    alertify.confirm(title,
        `
        ${fileinputs}
        <div class="w3-row">
            <div class="w3-row" id="handle-file-upload-view">
                
            </div>
            <div class="w3-row w3-center">
                <button class="primary" id="handle-file-upload-action">${Icon('add')}Add file</button>
            </div>
        </div>
        `,
        ()=>{},
        ()=>{}
    ).set('closable', false).set('labels',{ok:'Done', cancel:'Discard'})
    
    getElement('handle-file-upload-action').onclick=_=>{
        inputIDs.some((inp)=>{
            if(!getElement(inp).files[0]){
                getElement(inp).onchange=async(e)=>{
                    let b64 = await fileToBase64(Array.from(e.target.files)[0])
                    if(!b64) return
                    getElement('handle-file-upload-view').innerHTML+=`<input type='text' `
                    fileoutputs.some((out)=>{if(`handle-file-input-${out.id}`===inp){
                        out.value = b64
                        return true
                    }})
                }
                getElement(inp).click()
                return true
            }
            return false
        })
    }
}

const handleMultiFileUpload = (
    limit=3,
    onSubmit = (files) => {}
) => {
    let multiFiles = [];
    alertify.confirm("Multiple Files Upload",
        `
        <div class="container">
            <form id="form" action="">
                <div hidden>
                    <label for="upload">
                        <input type="file" class="file positive" id="input multifile" hidden>
                        <button class="active" type="button" data-icon="upload"><label for="input multifile" id="mutlifilebutton">Add Files</label></button><br/><br/>
                        Upload Files
                    </label>
                </div>
                <div class="files">
                    <h2>Files Selected</h2>
                    <div id="ul" class="w3-row">
                        <div class="w3-col w3-third w3-padding-small w3-center"  id="addperksbutton">
                            <div class="pallete primary pointer">
                                <i class="w3-jumbo material-icons positive-text">add_circle</i>
                                <label for="upload">
                                    <input type="file" class="file positive" id="input multifile" hidden>
                                    <button class="active" type="button" data-icon="upload"><label for="input multifile" id="mutlifilebutton">Add Files</label></button><br/>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </form>	
        </div>
        `,
        () => {
            onSubmit(multiFiles)
        },
        ()=>{}
    ).set('closable', false).set('labels',{ok:'Done', cancel:'Discard'})
    
    
   

        // event handlers
        document.getElementById("input multifile").onchange= async (e) => {
            let files = e.target.files;
            // let filesArr = Array.from(files);
            for (var data of multiFiles) {
                if (data.name == files[0].name) {
                    return;
                }
            }
            multiFiles.push({ id:Date.now(),name: files[0].name, size: files[0].size, content: await fileToBase64(files[0]) });
            renderFileList();
        };

       
        document.getElementById("form").onsubmit= function(e) {
            e.preventDefault();
            renderFileList();
        };

        // render functions
    function renderFileList() {
        if (multiFiles.length > limit) {
            error("Limit Exceeded");
        } else {
            document.getElementById("ul").innerHTML = ``;
            multiFiles.forEach((file, index) => {
                let suffix = "bytes";
                let size = file.size;
                if (size >= 1024 && size < 1024000) {
                    suffix = "KB";
                    size = Math.round(size / 1024 * 100) / 100;
                } else if (size >= 1024000) {
                    suffix = "MB";
                    size = Math.round(size / 1024000 * 100) / 100;
                }

                document.getElementById("ul").innerHTML += `<div key="${index}" class="w3-col w3-third">
                                                                <div class="w3-padding-small w3-center">
                                                                    <div class="pallete accent">
                                                                        <i class="w3-jumbo material-icons">folder</i>
                                                                        <input class="wide file-size" id="name_${file.id}" type="text" value="${file.name}"></input><i class="material-icons md-48 delete-files" id=${file.id} value=${file.id}>delete</i><label  for="name_${file.id}"></label>
                                                                    </div>
                                                                </div>
                                                            </div>
            `;
            });
            document.getElementById("ul").innerHTML += ` <div class="w3-col w3-third w3-padding-small w3-center"  id="addperksbutton">
                                                            <div class="pallete primary pointer">
                                                                <i class="w3-jumbo material-icons positive-text">add_circle</i>
                                                                <label for="upload">
                                                                    <input type="file" class="file positive" id="input multifile" hidden>
                                                                    <button class="active" type="button" data-icon="upload"><label for="input multifile" id="mutlifilebutton">Add Files</label></button><br/>
                                                                </label>
                                                            </div>
                                                        </div>`;
        }

        for (var data of multiFiles) {
            const ele = document.getElementById(`name_${data.id}`);
            ele.addEventListener("change", (e) => {
                data.name = ele.value;
            })
        }

        for (var data of multiFiles) {
            const ele = document.getElementById(data.id);

            ele.addEventListener ("click", (e) => {
                const newArr = multiFiles.filter(file =>  ele.id != file.id);
                multiFiles = newArr;
                renderFileList();
            })
        }
    }
    
    const delFunc = (e) => {
        // let key = document.body.parentNode.dataset.key;
        // console.log("Files click",document.body.parentNode.className);
        // console.log("Files key",document.body.parentNode.dataset.key);
        multiFiles.splice(e.value, 1);
        renderFileList();
    };
}


const handleDropDowns = (dropdownClassName, dropdownID, optionValues) => {
    const dropdown = getElement(dropdownID);
    const selectedOptionDiv = document.createElement("div");
    const dropdown_ul = document.createElement("ul");
    dropdown_ul.className = "dropdown-options-list pallete";
    selectedOptionDiv.className = "selected-option";
    setHtmlContent(selectedOptionDiv, optionValues[0]);
    dropdown.append(selectedOptionDiv, dropdown_ul);

    selectedOptionDiv.addEventListener("click", () => {
        show(dropdown_ul);
    });

    optionValues.forEach((item) => {
        const dropdown_li = document.createElement("li");
        dropdown_li.className = "dropdown-option";
        setHtmlContent(dropdown_li, item);
        dropdown_ul.append(dropdown_li);

        dropdown_li.addEventListener("click", () => {
            setHtmlContent(selectedOptionDiv, item);
            hide(dropdown_ul);
        });
    });

    window.addEventListener("click", (e) => {
        if (e.target !== selectedOptionDiv) {
            hide(dropdown_ul);
        }
    });
};

const handleInputDropdowns = ({
    dropdownID = "inputDropdown",
    inputDropdownOptionValues = [],
    inputType = "text",
    placeholder = "Start typing",
    onInput = ({
        inputField,
        listContainer,
        createList = (list = []) => {},
    }) => {},
    onChange = ({
        inputField,
        listContainer,
        createList = (list = []) => {},
    }) => {},
}) => {
    const inputDropdown = getElement(dropdownID);
    const inputField = document.createElement("input");
    const input_dropdown_ul = document.createElement("ul");
    input_dropdown_ul.className = "input-dropdown-options-list pallete";
    inputField.className = "input-dropdown-input-field";

    inputField.addEventListener("click", () => {
        show(input_dropdown_ul);
    });

    inputField.type = inputType;
    inputField.placeholder = placeholder;
    inputDropdown.append(inputField, input_dropdown_ul);

    const createList = (list) => {
        list.forEach((item) => {
            const input_dropdown_li = document.createElement("li");
            input_dropdown_li.className = "input-dropdown-option";
            setHtmlContent(input_dropdown_li, item);
            input_dropdown_ul.append(input_dropdown_li);
            input_dropdown_li.addEventListener("click", () => {
                inputField.value = item;
                hide(input_dropdown_ul);
            });
        });
    };

    createList(inputDropdownOptionValues);

    inputField.addEventListener("input", () => {
        onInput({ inputField, createList, listContainer: input_dropdown_ul });
    });

    inputField.addEventListener("change", () => {
        onChange({ inputField, createList, listContainer: input_dropdown_ul });
    });

    window.addEventListener("click", (e) => {
        if (e.target !== inputField) {
            hide(input_dropdown_ul);
        }
    });
};

const loadReporters = () => {
    getElements("report-button").forEach((report) => {
        report.type = "button";
        report.onclick = (_) => {
            reportFeedbackView();
        };
    });
};

const NegativeText = (text = "") =>
    `<span class="negative-text">${text}</span>`;

const PositiveText = (text = "") =>
    `<span class="positive-text">${text}</span>`;

const secsToTime = (secs) => {
    secs = Number(secs);
    let mins = secs / 60;
    let secrem = Math.floor(secs % 60);
    if (mins < 60) {
        mins = Math.floor(mins);
        return `${mins >= 10 ? mins : `0${mins}`}:${
            secrem >= 10 ? secrem : `0${secrem}`
        }`;
    }
    let hours = mins / 60;
    let minrem = Math.floor(mins % 60);
    if (hours < 24) {
        hours = Math.floor(hours);
        return `${hours >= 10 ? hours : `0${hours}`}:${
            minrem >= 10 ? minrem : `0${minrem}`
        }:${secrem >= 10 ? secrem : `0${secrem}`}`;
    }
    let days = Math.floor(hours / 24);
    let hourrem = Math.floor(hours % 24);
    return `${days >= 10 ? days : `0${days}`}:${
        hourrem >= 10 ? hourrem : `0${hourrem}`
    }:${minrem >= 10 ? minrem : `0${minrem}`}:${
        secrem >= 10 ? secrem : `0${secrem}`
    }`;
};

const reportFeedback = async ({
    isReport = true,
    email = "",
    category = "",
    summary = "",
    detail = "",
}) => {
    const data = await postRequest(
        isReport
            ? URLS.CREATE_REPORT || URLS.Management.CREATE_REPORT
            : URLS.CREATE_FEED || URLS.Management.CREATE_FEED,
        {
            email,
            category,
            summary,
            detail,
        }
    );
    if (!data) return false;
    if (data.code === code.OK) {
        success(
            `${
                isReport ? "Report" : "Feedback"
            } received and will be looked into.`
        );
        return true;
    }
    error(data.error);
    return false;
};

const reportFeedbackView = (report = 0) => {
    let isReport = false;
    const dial = alertify;
    dial.confirm().set({
        onshow: () =>
            initializeTabsView({
                tabsClass: "report-feed-tab",
                uniqueID: "reportFeed",
                viewID: false,
                onEachTab: (tab) => {
                    isReport = tab.id === "report";
                    getElements("report-feed-view").forEach((view) => {
                        visible(view, `${tab.id}-view` === view.id);
                    });
                },
                tabindex: report,
            }),
    });
    dial.confirm(
        `Report or Feedback`,
        `
        <div class="w3-row w3-center">
            <button class="report-feed-tab" id="report">${Icon(
                "flag"
            )} Report</button>
            <button class="report-feed-tab" id="feedback">${Icon(
                "feedback"
            )} Feedback</button>
        </div>
        <br/>
        <div class="w3-row w3-center">
            <h6>Your identity will remain private.</h6>
            <input class="wide" type="email" autocomplete="email" id="report-feed-email" placeholder="Your email address (optional)" /><br/><br/>
            <div class="w3-row w3-center report-feed-view" id="report-view">
                <textarea class="wide" rows="3" id="report-feed-summary" placeholder="Short description" ></textarea><br/><br/>
                <textarea class="wide" rows="5" id="report-feed-detail" placeholder="Explain everything here in detail" ></textarea>
            </div>
            <div class="w3-row report-feed-view" id="feedback-view">
                <textarea class="wide" rows="6" id="report-feed-feed-detail" placeholder="Please describe your feedback" ></textarea>
            </div>
        </div>
        `,
        async () => {
            let data = {};
            if (isReport) {
                const summary = String(
                    getElement("report-feed-summary").value
                ).trim();
                if (!summary) {
                    error("Short description required");
                    return false;
                }
                data["summary"] = summary;
                data["detail"] = String(
                    getElement("report-feed-detail").value
                ).trim();
            } else {
                const detail = String(
                    getElement("report-feed-feed-detail").value
                ).trim();
                if (!detail) {
                    error("Feedback description required");
                    return false;
                }
                data["detail"] = detail;
            }
            loader();
            data["isReport"] = isReport;
            data["email"] = String(
                getElement("report-feed-email").value
            ).trim();
            message(`Submitting ${isReport ? "report" : "feedback"}...`);
            await reportFeedback(data);
            loader(false);
        },
        () => {}
    )
        .set("labels", {
            ok: "Submit",
            cancel: "Discard",
        })
        .set("closable", false)
        .set("transition", "flipx");
};

const previewImageDialog = (src) => {
    if (!src) return;
    getElement("image-previewer").style.display = "flex";
    getElement("image-previewer").addEventListener("click", (e) => {
        if (e.target.id !== "preivew-image-src") {
            e.target.style.display = "none";
        }
    });
    getElement("preivew-image-src").src = src;
};

const futuremessage = (message = "") => {
    localStorage.setItem(Key.futureMessage, message);
};

const radarChartView = (
    chartCanvas,
    labels = [],
    labelsData = [],
    colorhex = "f5d702"
) => {
    return new Chart(chartCanvas.getContext("2d"), {
        type: "radar",
        data: {
            labels: labels,
            datasets: [
                {
                    data: labelsData,
                    borderColor: `#${colorhex}`,
                    backgroundColor: `#${colorhex}55`,
                },
            ],
        },
        options: {
            maintainAspectRatio: !false,
            scale: {
                ticks: {
                    display: false,
                    maxTicksLimit: 2,
                },
            },
            responsive: true,
            gridLines: {
                display: false,
            },
            plugins: {
                legend: false,
                tooltip: false,
                title: {
                    display: false,
                    text: "",
                },
            },
        },
    });
};

const getNumberSuffix = (value) => {
    let valuestr = String(value);
    switch (value) {
        case 1:
            return "st";
        case 2:
            return "nd";
        case 3:
            return "rd";
        default: {
            if (value > 9) {
                if (
                    valuestr[valuestr.length - 2] === "1" ||
                    valuestr[valuestr.length - 1] === "0"
                )
                    return "th";
                return getNumberSuffix(
                    (value = Number(valuestr[valuestr.length - 1]))
                );
            } else return "th";
        }
    }
};

const numsuffix = (number) => `${number}${getNumberSuffix(number)}`;
const connectWithGithub = (next = URLS.ROOT, oncancel = (_) => {}) => {
    alertify
        .alert(
            "Github ID Required",
            `<div class="w3-row w3-padding">
    <h4>Your Github identity must be linked with Knotters for this action.</h4>
    <br/>
    <a href="${URLS.Auth.GITHUB}login/?process=connect&next=${URLS.REDIRECTOR}?n=${next}">
        <button type="button" class="secondary"><img src="/static/graphics/thirdparty/github-dark.png" width="20" />
        &nbsp;+ <img src="${ICON}" width="22" /> ${APPNAME} <i class="material-icons">open_in_new</i>
        </button>
    </a>
    </div>`,
            () => {
                oncancel();
            }
        )
        .set("closable", false)
        .set("label", "Cancel");
};

const restartIntros = () => {
    Object.keys(localStorage).forEach((key) => {
        if (key.startsWith("first-intro-")) {
            localStorage.removeItem(key);
        }
    });
};

const betaAlert = () => {
    if (window.location.host.startsWith("beta.")||1) {
        alertify
            .confirm(
                "<h6>This is Knotters Beta</h6>",
                `<h5>Welcome to Knotters Beta, the pre-stable version of Knotters.
                New features become available here before Knotters.<br/>
                You'll have to create an account here separately from Knotters. None of the information at Knotters will be made available here.<br/>
                By continuing, you accept that for any of your data loss at Knotters Beta due to any error, you will solely be responsible.
            </h5>
            <h5>
                You can go to the stable Knotters (knotters.org) if you're here by mistake.
            </h5>
            `,
                () => {
                    window.location.href = window.location.href.replace(
                        "//beta.",
                        "//"
                    );
                },
                () => {
                    window.sessionStorage.setItem('beta-alerted', 1)
                    message("Remember, you're using Knotters Beta.");
                }
            )
            .set("closable", false)
            .set("labels", {
                ok: "Go to Knotters",
                cancel: "Stay in Knotters Beta",
            });
    }
};
