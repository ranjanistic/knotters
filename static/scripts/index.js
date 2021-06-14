"use strict";

const getElement = (id) => document.getElementById(id);

const getElements = (classname) =>
    Array.from(document.getElementsByClassName(classname));

const getElementsByTag = (tagname) =>
    Array.from(document.getElementsByTagName(tagname));

const loader = (show = true) => visibleElement("viewloader", show);

const openSpinner = (id = "loader") => showElement(id);

const hideSpinner = (id = "loader") => hideElement(id);

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

const loaderHTML = (loaderID="loader") => `<div class="loader" id="${loaderID}"></div>`;
const loadErrorHTML = (retryID) => `<div class="w3-center w3-padding-32">
<i class="negative-text material-icons w3-jumbo">error</i>
<h3>Oops. Something wrong here?</h3><button class="primary" id="${retryID}">Retry</button></div></div>`;

const intializeTabsView = (
    onEachTab = async (tabID) => {},
    uniqueID,
    tabsClass = "nav-tab",
    activeTabClass = "positive",
    inactiveTabClass = "primary",
    viewID = "tabview",
    spinnerID = "loader"
) => {
    const tabs = getElements(tabsClass),
        tabview = getElement(viewID);

    const showTabLoading = () => {
        tabview.innerHTML = loaderHTML(spinnerID);
        openSpinner(spinnerID);
    };

    const showTabError = (tabindex = 0) => {
        tabview.innerHTML = loadErrorHTML(`${uniqueID}retry`);
        getElement(`${uniqueID}retry`).onclick = (_) => tabs[tabindex].click();
    };

    const showTabContent = (content) => {
        tabview.innerHTML = content;
        loadGlobalEditors();
    };

    tabs.forEach(async (tab, t) => {
        tab.onclick = async () => {
            showTabLoading();
            sessionStorage.setItem(uniqueID, t);
            tabs.forEach((tab1, t1) => {
                if (t1 === t) {
                    tab1.classList.add(activeTabClass);
                    tab1.classList.remove(inactiveTabClass);
                } else {
                    tab1.classList.remove(activeTabClass);
                    tab1.classList.add(inactiveTabClass);
                }
            });
            const response = await onEachTab(tab.id);
            hideSpinner(spinnerID);
            return response ? showTabContent(response) : showTabError(t);
        };
    });

    tabs[Number(sessionStorage.getItem(uniqueID)) || 0].click();
};

const postRequest = async (path, data = {}) => {
    const body = { ...data };
    console.log(body);
    try {
        const response = await fetch(path, {
            method: "POST",
            headers: {
                Accept: "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrfmiddlewaretoken,
            },
            body: JSON.stringify(body),
        });
        console.log(await response.status);
        return await response;
    } catch (e) {
        console.log(e);
        return e;
    }
};

const getRequest = async (url) => {
    const response = await window.fetch(url, {
        method: "GET",
        headers: {
            "X-CSRFToken": csrfmiddlewaretoken,
        },
    });
    if (response.status - 200 > 100) return false;
    return response.text();
};

const loadGlobalEditors = (onSave = (_) => {}, onDiscard) => {
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
        navigator
            .share({ title, text, url })
            .then(() => {
                afterShared();
            })
            .catch(console.error);
    } else {
        alert("Sharing not available on your system.");
    }
};

document.addEventListener("DOMContentLoaded", () => {
    getElementsByTag("form").forEach((form) => {
        form.addEventListener("submit", (e) => {
            if (form.classList.contains("no-auto")) {
                e.preventDefault();
            }
        });
    });
});
// loader()
// window.onload=_=>loader(false);
