"use strict";

const Key = {
    appUpdated: "app-updated",
};

const code = {
    OK: "OK",
    NO: "NO",
};

const logOut = async (
    afterLogout = (_) => {
        window.location.replace("/");
    }
) => {
    const done = await postRequest("/auth/logout/");
    if (!done.location) return error("Failed to logout");
    message("Logged out successfully");
    afterLogout();
};

const getElement = (id) => document.getElementById(id);

const getElements = (classname) =>
    Array.from(document.getElementsByClassName(classname));

const getElementsByTag = (tagname) =>
    Array.from(document.getElementsByTagName(tagname));

const loader = (show = true) => visibleElement("viewloader", show);
const subLoader = (show = true) => visibleElement("subloader", show);
const loaders = (show = true) => {
    loader(show);
    subLoader(show);
};

const openSpinner = (id = "loader") => showElement(id);

const hideSpinner = (id = "loader") => hideElement(id);

const csrfHiddenInput = (token) =>
    `<input type="hidden" name="csrfmiddlewaretoken" value="${token}"></input>`;

const hide = (element) => {
    element.hidden = true;
    element.style.display = "none";
};
const show = (element) => {
    element.hidden = false;
    element.style.display = "block";
};

const hideElement = (id) => visibleElement(id, false);

const showElement = (id) => visibleElement(id, true);

const visibleElement = (id, show = true) => {
    getElement(id).hidden = show ? false : true;
    getElement(id).style.display = show ? "block" : "none";
};

const visible = (element,show=true) => visibleElement(element.id, show);

const miniWindow = (url, name = APPNAME) =>
    window.open(url, name, "height=650,width=450");

const message = (msg = "") => {
    alertify.set("notifier", "position", "top-left");
    alertify.message(msg);
};

const error = (msg = "An error occurred") => {
    alertify.set("notifier", "position", "bottom-right");
    alertify.error(msg);
};

const success = (msg = "Success") => {
    alertify.set("notifier", "position", "top-right");
    alertify.success(msg);
};

const loaderHTML = (loaderID = "loader") =>
    `<div class="loader" id="${loaderID}"></div>`;
const loadErrorHTML = (retryID='retryload') => `<div class="w3-center w3-padding-32">
<i class="negative-text material-icons w3-jumbo">error</i>
<h3>Oops. Something wrong here?</h3><button class="primary" id="${retryID}">Retry</button></div></div>`;

const setHtmlContent = (element, content = "", afterset=()=>{}) => {
    element.innerHTML = content;
    loadGlobalEventListeners();
    loadGlobalEditors();
    loadCarousels({});
    afterset()
};

const setUrlParams = (path, ...params) => {
    params.forEach((param) => {
        path = String(path).replace("*", param);
    });
    return path;
};

const loadGlobalEventListeners = () => {
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
            !a.getAttribute("target")
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
                button.innerHTML = `${Icon(button.getAttribute("data-icon"))}${button.innerHTML}`;
            }
        }
    });
    getElementsByTag("i").forEach((icon) => {
        icon.classList.add("material-icons");
    });
};

const Icon = (name, classnames='') => `<i class="material-icons ${classnames}">${name}</i>`;

const loadCarousels = ({
    container = "swiper-container",
    loop = false,
    grabCursor = true,
    spaceBetween = 5,
    breakpoints = {
        640: {
            slidesPerView: 1,
            spaceBetween: 0,
        },
        768: {
            slidesPerView: 1,
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
}) => {
    const tabs = getElements(tabsClass);
    let tabview = null;
    try{
        tabview = getElement(viewID)
    } catch{}        

    const showTabLoading = () => {
        if(tabview){
            setHtmlContent(tabview, loaderHTML(spinnerID));
            openSpinner(spinnerID);
        }
    };

    const showTabError = (tab) => {
        if(tabview){
            setHtmlContent(tabview, loadErrorHTML(`${uniqueID}retry`));
            getElement(`${uniqueID}retry`).onclick = (_) => tab.click();
        }
    };

    const showTabContent = (tab, content) => {
        if(tabview){
            setHtmlContent(tabview, content);
        }
        onShowTab(tab);
    };

    tabs.forEach(async (tab, t) => {
        tab.onclick = async () => {
            showTabLoading();
            sessionStorage.setItem(uniqueID, t);
            const onclicks = Array(tabs.length);
            tabs.forEach((tab1, t1) => {
                onclicks[t1] = tab1.onclick;
                tab1.onclick = (_) => {};
                if (t1 === t) {
                    activeTabClass.split(' ').forEach((active)=>tab1.classList.add(active))
                    inactiveTabClass.split(' ').forEach((inactive)=>tab1.classList.remove(inactive))
                } else {
                    tab1.style.opacity = 0;
                    activeTabClass.split(' ').forEach((active)=>tab1.classList.remove(active))
                    inactiveTabClass.split(' ').forEach((inactive)=>tab1.classList.add(inactive))
                }
            });
            const response = await onEachTab(tab);
            if(tabview) hideSpinner(spinnerID);
            tabs.forEach((tab1, t1) => {
                if (t1 !== t) {
                    tab1.style.opacity = 1;
                }
                tab1.onclick = onclicks[t1];
            });
            return response ? showTabContent(tab, response) : showTabError(tab);
        };
    });
    if (tabs.length) {
        try {
            tabs[Number(sessionStorage.getItem(uniqueID)) || 0].click();
        } catch (e) {
            tabs[selected].click();
        }
    }
    return tabs;
};

const initializeMultiSelector = ({
    candidateClass = "multi-select-candidate",
    selectedClass = 'positive',
    deselectedClass = 'primary',
    onSelect = async (candidate) => true,
    onDeselect = async (candidate) => true,
    uniqueID = String(Math.random()),
}) => {
    const candidates = getElements(candidateClass);
    let selectedlist = [], deselectedList = candidates;
    candidates.forEach((candidate)=>{
        candidate.addEventListener('click',()=>{
            if (deselectedList.includes(candidate)){
                if(onSelect(candidate)){
                    deselectedList = deselectedList.filter((cand)=>cand!=candidate)
                    selectedlist.push(candidate)
                    deselectedClass.split(' ').forEach((cl)=>{
                        if(cl) candidate.classList.remove(cl)
                    })
                    selectedClass.split(' ').forEach((cl)=>{
                        if(cl) candidate.classList.add(cl)
                    })
                }
            } else if(selectedlist.includes(candidate)){
                if(onDeselect(candidate)){
                    selectedlist = selectedlist.filter((cand)=>cand!=candidate)
                    deselectedList.push(candidate)
                    deselectedClass.split(' ').forEach((cl)=>{
                        if(cl) candidate.classList.add(cl)
                    })
                    selectedClass.split(' ').forEach((cl)=>{
                        if(cl) candidate.classList.remove(cl)
                    })
                }
            }
        })
    })
    return candidates
}

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
                "X-KNOT-REQ-SCRIPT": true
            },
            body: JSON.stringify(body),
        });
        const data = await response.json();
        subLoader(false);
        return data;
    } catch (e) {
        error('An error occurred');
        subLoader(false);
        return false;
    }
};

const getRequest = async (url) => {
    try {
        subLoader();
        const response = await window.fetch(url, {
            method: "GET",
            headers: {
                "X-CSRFToken": csrfmiddlewaretoken,
                "X-KNOT-REQ-SCRIPT": true
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
    if (navigator.share) {
        subLoader()
        navigator.share({ title, text, url }).then(() => {
            subLoader(false)
            afterShared();
        }).catch(()=>{
            subLoader(false)
            error("Failed to share")
        });
    } else {
        error("Sharing not available on your system.");
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
                        getElement(dataOutElemID).value = croppedB64;
                        getElement(previewImgID).src = croppedB64;
                        onCropped(croppedB64);
                    } catch (e) {
                        error(
                            `An error occurred. <br/><button class="small primary" onclick="window.location.reload();">Reload</button>`
                        );
                    }
                },
                () => {}
            )
            .set("closable", false)
            .set('labels',{
                ok: 'Confirm',
                cancel: 'Cancel'
            });
        const cropImage = new Cropper(getElement("tempprofileimageoutput"), {
            aspectRatio: ratio,
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
            alertify
                .confirm(
                    "Report or Feedback",
                    `<h4>What's going on?</h4>`,
                    () => {
                        subLoader(true);
                        message("Reporting...");
                        localStorage.setItem(Key.appUpdated, 1);
                    },
                    () => {}
                )
                .set("labels", { ok: "Submit", cancel: "Cancel" });
        };
    });
};

const NegativeText = (text = "") =>
    `<span class="negative-text">${text}</span>`;

const secsToTime = (secs) => {
    secs = Number(secs)
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
    email = '',
    category = '',
    summary = '',
    detail = ''
}) => {
    const data = await postRequest(URLS.REPORT_FEEDBACK,{
        isReport,
        email,
        category,
        summary,
        detail
    })
    if(!data) return false
    if(data.code===code.OK) {
        success(`${isReport?'Report':'Feedback'} received and will be looked into.`)
        return true
    }
    error(data.error)
    return false
}

const reportFeedbackView = () => {
    let isReport = false;
    const dial = alertify;
    dial.confirm().set({onshow: ()=>
        initializeTabsView({
            tabsClass: 'report-feed-tab',
            onEachTab: (tab)=>{
                isReport = tab.id === 'report'
                getElements('report-feed-view').forEach((view)=>{
                    visible(view,`${tab.id}-view`===view.id)
                })
            }
        })
    })
    dial.confirm(
        `Report or Feedback`,
        `
        <div class="w3-row w3-center">
            <button class="report-feed-tab" id="report">${Icon('flag')} Report</button>
            <button class="report-feed-tab" id="feedback">${Icon('feedback')} Feedback</button>
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
        async ()=>{
            let data = {}
            if(isReport){
                const summary = String(getElement('report-feed-summary').value).trim()
                if(!summary) return error('Short description required')
                data['summary'] = summary
                data['detail'] = String(getElement('report-feed-detail').value).trim()
            } else {
                const detail = String(getElement('report-feed-feed-detail').value).trim()
                if(!detail) return error('Feedback description required')
                data['detail'] = detail
            }
            loader()
            data['isReport'] = isReport
            data['email'] = String(getElement("report-feed-email").value).trim()
            message(`Submitting ${isReport?'report':'feedback'}...`)
            await reportFeedback(data)
            loader(false)
        },
        ()=>{}
    ).set('labels', {
        ok: 'Submit',
        cancel: 'Discard'
    }).set('closable',false).set('transition','flipx')
}
