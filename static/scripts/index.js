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

const postRequest = async (path, data = {}) => {
    const body = { ...data };
    const response = await window.fetch(path, {
        method: "POST",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": csrfmiddlewaretoken,
        },
        body,
    });
    return response.json();
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

const loadGlobalEditors = () => {
    getElements("edit-action").forEach((edit) => {
        const target = edit.getAttribute("data-edittarget"),
            viewer = getElement(`view-${target}`),
            editor = getElement(`edit-${target}`),
            discard = getElement(`discard-edit-${target}`),
            save = getElement(`save-edit-${target}`);
        hide(editor);
        show(viewer);
        save.classList.add("positive");
        discard.classList.add("negative");
        edit.onclick = (_) => {
            hide(viewer);
            show(editor);
            discard.onclick = (_) => {
                hide(editor);
                show(viewer);
            };
            save.onclick = (_) => {
                hide(editor);
                show(viewer);
            };
        };
    });
};

document.addEventListener("DOMContentLoaded", () => {
    getElementsByTag("form").forEach((form) => {
      form.addEventListener("submit", (e) => {
        // e.preventDefault();
      });
    });
});
// loader()
// window.onload=_=>loader(false);
