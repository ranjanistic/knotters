if (selfProject) {
    getElement("uploadprojectimage").onchange = (e) => {
        handleCropImageUpload(
            e,
            "projectimageData",
            "projectimageoutput",
            (croppedB64) => {
                getElement("uploadprojectimagelabel").innerHTML = "Selected";
                getElement("projectimageoutput").style.opacity = 1;
            }
        );
    };

    const loadExistingTopics = () => {
        initializeMultiSelector({
            candidateClass: "topic-existing",
            selectedClass: "negative",
            deselectedClass: "primary negative-text",
            onSelect: (btn) => {
                if (!getElement("removetopicIDs").value.includes(btn.id))
                    getElement("removetopicIDs").value += getElement(
                        "removetopicIDs"
                    ).value
                        ? "," + btn.id
                        : btn.id;
                return true;
            },
            onDeselect: (btn) => {
                let addtopids = getElement("addtopicIDs").value.split(",");
                let addtoplen = addtopids.length;
                if (addtoplen === 1 && addtopids.includes("")) {
                    addtoplen = 0;
                }
                let remtopids = getElement("removetopicIDs").value.split(",");
                let remtoplen = remtopids.length;
                if (remtoplen === 1 && remtopids.includes("")) {
                    remtoplen = 0;
                }
                if (
                    getElements("topic-existing").length -
                        remtoplen +
                        addtoplen ===
                    5
                ) {
                    error("Only upto 5 topics allowed");
                    return false;
                }
                let ids = getElement("removetopicIDs").value;
                ids = ids.replaceAll(btn.id, "");
                if (ids.endsWith(",")) {
                    ids = ids.split(",");
                    ids.pop();
                    ids.join(",");
                }
                getElement("removetopicIDs").value = ids;
                return true;
            },
        });
    };
    const loadNewTopics = () => {
        initializeMultiSelector({
            candidateClass: "topic-new",
            selectedClass: "positive",
            deselectedClass: "primary",
            onSelect: (btn) => {
                let addtopids = getElement("addtopicIDs").value.split(",");
                let addtoplen = addtopids.length;
                if (addtoplen === 1 && addtopids.includes("")) {
                    addtoplen = 0;
                }
                let remtopids = getElement("removetopicIDs").value.split(",");
                let remtoplen = remtopids.length;
                if (remtoplen === 1 && remtopids.includes("")) {
                    remtoplen = 0;
                }
                if (
                    getElements("topic-existing").length -
                        remtoplen +
                        addtoplen ===
                    5
                ) {
                    error("Only upto 5 topics allowed");
                    return false;
                }
                if (!getElement("addtopicIDs").value.includes(btn.id))
                    getElement("addtopicIDs").value += getElement("addtopicIDs")
                        .value
                        ? "," + btn.id
                        : btn.id;
                return true;
            },
            onDeselect: (btn) => {
                let ids = getElement("addtopicIDs").value;
                ids = ids.replaceAll(btn.id, "");
                if (ids.endsWith(",")) {
                    ids = ids.split(",");
                    ids.pop();
                    ids.join(",");
                }
                getElement("addtopicIDs").value = ids;
                return true;
            },
        });
    };
    let lastquery = "";
    getElement("topic-search-input").oninput = async (e) => {
        if (!e.target.value.trim()) return;
        if (e.target.value.length != lastquery.length) {
            if (e.target.value.length < lastquery.length) {
                lastquery = e.target.value;
                return;
            } else {
                lastquery = e.target.value;
            }
        }
        getElement("topics-viewer-new").innerHTML = "";
        const data = await postRequest(
            setUrlParams(URLS.TOPICSEARCH, projectID),
            {
                query: e.target.value,
            }
        );
        if (!data) return;
        if (data.code === code.OK) {
            let buttons = [];
            data.topics.forEach((topic) => {
                buttons.push(
                    `<button type="button" class="${
                        getElement("addtopicIDs").value.includes(topic.id)
                            ? "positive"
                            : "primary"
                    } topic-new" id="${topic.id}">${Icon("add")}${
                        topic.name
                    }</button>`
                );
            });
            if (buttons.length) {
                getElement("topics-viewer-new").innerHTML = buttons.join("");
                loadNewTopics();
                loadExistingTopics();
            } else {
                getElement(
                    "topics-viewer-new"
                ).innerHTML = `No topics for '${e.target.value}'`;
            }
        } else {
            error(data.error);
        }
    };
    loadExistingTopics();

    const loadExistingTags = () => {
        initializeMultiSelector({
            candidateClass: "tag-existing",
            selectedClass: "negative",
            deselectedClass: "primary negative-text",
            onSelect: (btn) => {
                if (!getElement("removetagIDs").value.includes(btn.id))
                    getElement("removetagIDs").value += getElement(
                        "removetagIDs"
                    ).value
                        ? "," + btn.id
                        : btn.id;
                return true;
            },
            onDeselect: (btn) => {
                let addtopids = getElement("addtagIDs").value.split(",");
                let addtoplen = addtopids.length;
                if (addtoplen === 1 && addtopids.includes("")) {
                    addtoplen = 0;
                }
                let remtopids = getElement("removetagIDs").value.split(",");
                let remtoplen = remtopids.length;
                if (remtoplen === 1 && remtopids.includes("")) {
                    remtoplen = 0;
                }
                if (
                    getElements("tag-existing").length -
                        remtoplen +
                        addtoplen ===
                    5
                ) {
                    error("Only upto 5 tags allowed");
                    return false;
                }
                let ids = getElement("removetagIDs").value;
                ids = ids.replaceAll(btn.id, "");
                if (ids.endsWith(",")) {
                    ids = ids.split(",");
                    ids.pop();
                    ids.join(",");
                }
                getElement("removetagIDs").value = ids;
                return true;
            },
        });
    };
    const loadNewTags = () => {
        initializeMultiSelector({
            candidateClass: "tag-new",
            selectedClass: "positive",
            deselectedClass: "primary",
            onSelect: (btn) => {
                let addtopids = getElement("addtagIDs").value.split(",");
                let addtoplen = addtopids.length;
                if (addtoplen === 1 && addtopids.includes("")) {
                    addtoplen = 0;
                }
                let remtopids = getElement("removetagIDs").value.split(",");
                let remtoplen = remtopids.length;
                if (remtoplen === 1 && remtopids.includes("")) {
                    remtoplen = 0;
                }
                if (
                    getElements("tag-existing").length -
                        remtoplen +
                        addtoplen ===
                    5
                ) {
                    error("Only upto 5 tags allowed");
                    return false;
                }
                if (!getElement("addtagIDs").value.includes(btn.id))
                    getElement("addtagIDs").value += getElement("addtagIDs")
                        .value
                        ? "," + btn.id
                        : btn.id;
                return true;
            },
            onDeselect: (btn) => {
                let ids = getElement("addtagIDs").value;
                ids = ids.replaceAll(btn.id, "");
                if (ids.endsWith(",")) {
                    ids = ids.split(",");
                    ids.pop();
                    ids.join(",");
                }
                getElement("addtagIDs").value = ids;
                return true;
            },
        });
    };
    let lasttagquery = "";
    getElement("tag-search-input").oninput = async (e) => {
        if (!e.target.value.trim()) return;
        if (e.target.value.length != lasttagquery.length) {
            if (e.target.value.length < lasttagquery.length) {
                lasttagquery = e.target.value;
                return;
            } else {
                lasttagquery = e.target.value;
            }
        }
        getElement("tags-viewer-new").innerHTML = "";
        const data = await postRequest(
            setUrlParams(URLS.TAGSEARCH, projectID),
            {
                query: e.target.value,
            }
        );
        if (!data) return;
        if (data.code === code.OK) {
            let buttons = [];
            data.tags.forEach((tag) => {
                buttons.push(
                    `<button type="button" class="${
                        getElement("addtagIDs").value.includes(tag.id)
                            ? "positive"
                            : "primary"
                    } tag-new" id="${tag.id}">${Icon("add")}${
                        tag.name
                    }</button>`
                );
            });
            if (buttons.length) {
                getElement("tags-viewer-new").innerHTML = buttons.join("");
                loadNewTags();
                loadExistingTags();
            } else {
                getElement(
                    "tags-viewer-new"
                ).innerHTML = `No tags for '${e.target.value}'`;
            }
        } else {
            error(data.error);
        }
    };
    loadExistingTags();

    getElement("snap-file").onchange = (e) => {
        handleCropImageUpload(
            e,
            "snapimage",
            "snapimageview",
            (croppedB64) => {
                hide(getElement("add-image-view"));
                show(getElement("snapimageview"));
            },
            true
        );
    };
}

let snapstart = 0,
    snapend = snapstart + 10;
const snapsview = getElement(`snapshots-view`);

const addSnapsView = () => {
    const newsnapview = document.createElement("div");
    newsnapview.innerHTML = `<div class="w3-row" id="snapshots-view-${snapstart}"><div class="loader"></div></div>`;
    snapsview.insertBefore(
        newsnapview,
        snapsview.childNodes[Array.from(snapsview.childNodes).length - 1]
    );
};
const loadsnaps = getElement("load-more-snaps");

loadsnaps.onclick = (_) => {
    addSnapsView();
    const currentsnapsview = getElement(`snapshots-view-${snapstart}`);
    getRequest(
        setUrlParams(URLS.SNAPSHOTS, projectID, snapstart, snapend)
    ).then((data) => {
        if (data === false) {
            currentsnapsview.innerHTML = loadErrorHTML();
            return
        }
        if (!String(data).trim()) {
            if (snapstart < 1) {
                currentsnapsview.innerHTML = `<div class="dead-text" align="center">No snapshots yet</div>`;
            } else {
                currentsnapsview.innerHTML = `<div class="dead-text" align="center"><br/>No more snapshots</div>`;
            }
            return hide(loadsnaps);
        }
        setHtmlContent(currentsnapsview, data);
        snapstart = snapend;
        snapend = snapstart + 10;
        show(loadsnaps);
    });
};

loadsnaps.click();

const loadLiveData = async () => {
    const contribview = getElement("project-contibutors-view");
    const languageview = getElement("project-languages-view");
    if (contribview) setHtmlContent(contribview, loaderHTML());
    if (languageview) setHtmlContent(languageview, loaderHTML());
    if (contribview || languageview) {
        const data = JSON.parse(await getRequest(setUrlParams(URLS.LIVEDATA, projectID)))
        if (!data || data.code !== code.OK) {
            setHtmlContent(contribview, loadErrorHTML(`livecontdataretry`));
            setHtmlContent(languageview, loadErrorHTML(`livelangdataretry`));
            getElement(`livecontdataretry`).onclick = (_) => loadLiveData();
            getElement(`livelangdataretry`).onclick = (_) => loadLiveData();
            return;
        }
        if (contribview) setHtmlContent(contribview, data.contributorsHTML);
        if (languageview) {
            setHtmlContent(
                languageview,
                `<canvas id="project-languages-distribution-chart" class="chart-view" data-type="radar" width="400" height="400"></canvas>`
            );
            radarChartView(
                getElement("project-languages-distribution-chart"),
                Object.keys(data.languages),
                Object.keys(data.languages).map((key) => data.languages[key]),
                "12e49d"
            );
        }
    }
};
try {
    loadLiveData();
} catch (e) {
    console.debug(e);
}
