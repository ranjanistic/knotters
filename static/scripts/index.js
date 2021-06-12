"use strict";

const getElement = (id) => document.getElementById(id);

const getElements = (classname) =>
    Array.from(document.getElementsByClassName(classname));

const loader = (show = true) => visibleElement("viewloader", show);

const openSpinner = (id = "loader") => showElement(id);

const hideSpinner = (id = "loader") => hideElement(id);

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
    if(response.status-200>100) return false;
    return response.text();
};
