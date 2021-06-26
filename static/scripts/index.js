"use strict";

const Key = {
    appUpdated: "app-updated",
};

const serviceWorkerRegistration = () => {
    if (navigator.serviceWorker) {
        var newServiceWorker;
        const newUpdateBar = () => {
            alertify
                .confirm(
                    `Update available: ${VERSION}`,
                    `<h4>A new version of ${APPNAME} is available, with new features & performance improvements.<br/><br/>Shall we update?<h4>`,
                    () => {
                        alertify.message("Updating...");
						loader(true)
						localStorage.setItem(Key.appUpdated, 1)
                        newServiceWorker.postMessage({ action: "skipWaiting" });
                    },
                    () => {
                        alertify.message(
                            "We'll remind you later."
                        );
                    }
                ).set({'closable':false, ok: "Update", cancel: "Not now", "modal":true })
        };
        window.addEventListener("load", () => {
            navigator.serviceWorker
                .register("/service-worker.js")
                .then((reg) => {
                    if (reg.waiting) {
                        newServiceWorker = reg.waiting;
						newUpdateBar();
                    }
                    reg.addEventListener("updatefound", () => {
                        newServiceWorker = reg.installing;
                        newServiceWorker.addEventListener("statechange", () => {
                            switch (newServiceWorker.state) {
                                case "installed":
                                    if (navigator.serviceWorker.controller) {
                                        newUpdateBar();
                                    }
                                    break;
                            }
                        });
                    });
                })
                .catch((err) =>
                    console.log("Service worker not registered", err)
                );

				if(Number(localStorage.getItem(Key.appUpdated))){
					alertify.success('App updated successfully.')
					localStorage.removeItem(Key.appUpdated)
				}
        });
        let refreshing;
        navigator.serviceWorker.addEventListener("controllerchange", () => {
            if (refreshing) return;
            window.location.reload();
            refreshing = true;
        });
    }
};

const getElement = (id) => document.getElementById(id);

const getElements = (classname) =>
    Array.from(document.getElementsByClassName(classname));

const getElementsByTag = (tagname) =>
    Array.from(document.getElementsByTagName(tagname));

document.addEventListener("DOMContentLoaded", () => {
    getElementsByTag("form").forEach((form) => {
        form.addEventListener("submit", (e) => {
            if (form.classList.contains("no-auto")) {
                e.preventDefault();
            }
        });
    });
    getElements("href").forEach((href) => {
        href.addEventListener("click", (e) => {
            window.location.href = href.getAttribute("data-href");
        });
    });
    getElementsByTag("button").forEach((button) => {
        if (button.title) {
            let mPressTimer;
            button.addEventListener("touchstart", (e) => {
                mPressTimer = window.setTimeout(() => {
                    alertify.set("notifier", "position", "bottom-right");
                    alertify.message(button.title);
                }, 500);
                button.addEventListener("touchend", (e) => {
                    clearTimeout(mPressTimer);
                });
            });
        }
    });
    getElementsByTag("i").forEach((icon) => {
        if (icon.classList && icon.title) {
            let mPressTimer;
            icon.addEventListener("touchstart", (e) => {
                mPressTimer = window.setTimeout(() => {
                    alertify.set("notifier", "position", "bottom-right");
                    alertify.message(icon.title);
                }, 500);
                icon.addEventListener("touchend", (e) => {
                    clearTimeout(mPressTimer);
                });
            });
        }
    });
});

const loader = (show = true) => {
    getElement("viewloader").innerHTML = show
        ? `<div class="loader"></div>`
        : "";
    visibleElement("viewloader", show);
};

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

const loaderHTML = (loaderID = "loader") =>
    `<div class="loader" id="${loaderID}"></div>`;
const loadErrorHTML = (retryID) => `<div class="w3-center w3-padding-32">
<i class="negative-text material-icons w3-jumbo">error</i>
<h3>Oops. Something wrong here?</h3><button class="primary" id="${retryID}">Retry</button></div></div>`;

const initializeTabsView = (
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
            const onclicks = Array(tabs.length);
            tabs.forEach((tab1, t1) => {
                onclicks[t1] = tab1.onclick;
                tab1.onclick = (_) => {};
                if (t1 === t) {
                    tab1.classList.add(activeTabClass);
                    tab1.classList.remove(inactiveTabClass);
                } else {
                    tab1.style.opacity = 0;
                    tab1.classList.remove(activeTabClass);
                    tab1.classList.add(inactiveTabClass);
                }
            });
            const response = await onEachTab(tab.id);
            hideSpinner(spinnerID);
            tabs.forEach((tab1, t1) => {
                if (t1 !== t) {
                    tab1.style.opacity = 1;
                }
                tab1.onclick = onclicks[t1];
            });
            return response ? showTabContent(response) : showTabError(t);
        };
    });
    try {
        tabs[Number(sessionStorage.getItem(uniqueID)) || 0].click();
    } catch (e) {
        tabs[0].click();
    }
    return tabs;
};

const postRequest = async (path, data = {}) => {
    const body = { ...data };
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
        return await response.json();
    } catch (e) {
        return e;
    }
};

const getRequest = async (url) => {
    try {
        const response = await window.fetch(url, {
            method: "GET",
            headers: {
                "X-CSRFToken": csrfmiddlewaretoken,
            },
        });
        if (response.status - 200 > 100) return false;
        return response.text();
    } catch (e) {
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

loadGlobalEditors();

const shareLinkAction = (title, text, url, afterShared = (_) => {}) => {
    if (navigator.share) {
        navigator.share({ title, text, url }).then(() => {
            afterShared();
        });
    } else {
        alert("Sharing not available on your system.");
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

        dialog
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
                        alertify.error(
                            `An error occurred. <br/><button class="primary" onclick="window.location.reload();">Reload</button>`
                        );
                    }
                },
                () => {}
            )
            .set("closable", false);
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
  dropdown_ul.className = "dropdown-options-list";
  selectedOptionDiv.className = "selected-option";
  selectedOptionDiv.innerHTML = optionValues[0];
  dropdown.append(selectedOptionDiv, dropdown_ul);

  selectedOptionDiv.addEventListener("click", () => {
    show(dropdown_ul);
  });

  optionValues.forEach((item) => {
    const dropdown_li = document.createElement("li");
    dropdown_li.className = "dropdown-option";
    dropdown_li.innerHTML = item;
    dropdown_ul.append(dropdown_li);

    dropdown_li.addEventListener("click", () => {
      selectedOptionDiv.innerHTML = item;
      hide(dropdown_ul);
    });
  });

  window.addEventListener("click", (e) => {
    if (e.target !== selectedOptionDiv) {
        hide(dropdown_ul);
    }
  });
};

const handleInputDropdowns = (
  inputDropdownClassname,
  inputDropdownID,
  inputDropdownOptionValues
) => {
  const inputDropdown = getElement(inputDropdownID);
  const inputField = document.createElement("input");
  const input_dropdown_ul = document.createElement("ul");
  input_dropdown_ul.className = "input-dropdown-options-list";
  inputField.className = "input-dropdown-input-field";

  inputField.addEventListener("click", () => {
    show(input_dropdown_ul);
  });

  inputField.type = "text";
  inputField.placeholder = "Type or choose an option";
  inputDropdown.append(inputField, input_dropdown_ul);

  inputDropdownOptionValues.forEach((item) => {
    const input_dropdown_li = document.createElement("li");
    input_dropdown_li.className = "input-dropdown-option";
    input_dropdown_li.innerHTML = item;
    input_dropdown_ul.append(input_dropdown_li);

    input_dropdown_li.addEventListener("click", () => {
      inputField.value = item;
      hide(input_dropdown_ul);
    });
  });

  window.addEventListener("click", (e) => {
    if (e.target !== inputField) {
      hide(input_dropdown_ul);
    }
  });
};

