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
                const remtopIDselem = getElement("removetopicIDs");
                if (!remtopIDselem.value.includes(btn.id))
                    remtopIDselem.value += remtopIDselem.value
                        ? "," + btn.id
                        : btn.id;
                return true;
            },
            onDeselect: (btn) => {
                let addtopids = getElement("addtopicIDs")
                    .value.split(",")
                    .filter((x) => x);
                let addtops = getElement("addtopics")
                    .value.split(",")
                    .filter((x) => x);
                let addtoplen = addtopids.length + addtops.length;

                let remtopids = getElement("removetopicIDs")
                    .value.split(",")
                    .filter((x) => x);
                let remtoplen = remtopids.length;

                if (
                    getElements("topic-existing").length -
                        remtoplen +
                        addtoplen ===
                    5
                ) {
                    error("Only upto 5 topics allowed");
                    return false;
                }
                getElement("removetopicIDs").value = getElement(
                    "removetopicIDs"
                )
                    .value.replaceAll(btn.id, "")
                    .split(",")
                    .filter((x) => x)
                    .join(",");
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
                let addtopids = getElement("addtopicIDs")
                    .value.split(",")
                    .filter((x) => x);
                let addtops = getElement("addtopics")
                    .value.split(",")
                    .filter((x) => x);
                let addtoplen = addtopids.length + addtops.length;

                let remtopids = getElement("removetopicIDs")
                    .value.split(",")
                    .filter((x) => x);
                let remtoplen = remtopids.length;
                if (
                    getElements("topic-existing").length -
                        remtoplen +
                        addtoplen ===
                    5
                ) {
                    error("Only upto 5 topics allowed");
                    return false;
                }
                if (btn.classList.contains("topic-name")) {
                    if (!getElement("addtopics").value.includes(btn.id))
                        getElement("addtopics").value += getElement("addtopics")
                            .value
                            ? "," + btn.id
                            : btn.id;
                } else {
                    if (!getElement("addtopicIDs").value.includes(btn.id))
                        getElement("addtopicIDs").value += getElement(
                            "addtopicIDs"
                        ).value
                            ? "," + btn.id
                            : btn.id;
                }
                return true;
            },
            onDeselect: (btn) => {
                if (!btn.classList.contains("topic-name")) {
                    getElement("addtopicIDs").value = getElement("addtopicIDs")
                        .value.replaceAll(btn.id, "")
                        .split(",")
                        .filter((x) => x)
                        .join(",");
                } else {
                    getElement("addtopics").value = getElement("addtopics")
                        .value.replaceAll(btn.id, "")
                        .split(",")
                        .filter((x) => x)
                        .join(",");
                }
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
        const data = await postRequest2({
            path: setUrlParams(URLS.TOPICSEARCH, projectID), 
            data:{
                query: e.target.value,
            }
        });
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
                buttons.push(
                    `<button type="button" class="${
                        getElement("addtopics").value.includes(e.target.value)
                            ? "positive"
                            : "primary"
                    } topic-new topic-name" id="${e.target.value}">${Icon(
                        "add"
                    )}${e.target.value}</button>`
                );
                getElement("topics-viewer-new").innerHTML = buttons.join("");
                loadNewTopics();
                loadExistingTopics();
            }
        } else {
            error(data.error);
        }
    };
    loadExistingTopics();
    getElement("save-edit-projecttopics").onclick = async () => {
        const obj = getFormDataById("edit-project-topics-form");
        const resp = await postRequest2({
            path:setUrlParams(URLS.TOPICSUPDATE,projectID), 
            data:{
                addtopicIDs: obj.addtopicIDs.split(",").filter((x) => x),
                addtopics: obj.addtopics.split(",").filter((x) => x),
                removetopicIDs: obj.removetopicIDs.split(",").filter((x) => x),
            }
        });
        if (resp.code === code.OK){
            subLoader()
            return window.location.reload();
        }
        error(resp.error);
    };

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
                let addtagids = getElement("addtagIDs")
                    .value.split(",")
                    .filter((x) => x);
                let addtags = getElement("addtags")
                    .value.split(",")
                    .filter((x) => x);
                let addtaglen = addtagids.length + addtags.length;
                let remtagids = getElement("removetagIDs")
                    .value.split(",")
                    .filter((x) => x);
                let remtaglen = remtagids.length;
                if (
                    getElements("tag-existing").length -
                        remtaglen +
                        addtaglen ===
                    5
                ) {
                    error("Only upto 5 tags allowed");
                    return false;
                }

                getElement("removetagIDs").value = getElement("removetagIDs")
                    .value.replaceAll(btn.id, "")
                    .split(",")
                    .filter((x) => x)
                    .join(",");
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
                let addtagids = getElement("addtagIDs")
                    .value.split(",")
                    .filter((x) => x);
                let addtags = getElement("addtags")
                    .value.split(",")
                    .filter((x) => x);
                let addtaglen = addtagids.length + addtags.length;
                let remtagids = getElement("removetagIDs")
                    .value.split(",")
                    .filter((x) => x);
                let remtaglen = remtagids.length;

                if (
                    getElements("tag-existing").length -
                        remtaglen +
                        addtaglen ===
                    5
                ) {
                    error("Only upto 5 tags allowed");
                    return false;
                }
                if (btn.classList.contains("tag-name")) {
                    if (!getElement("addtags").value.includes(btn.id))
                        getElement("addtags").value += getElement("addtags")
                            .value
                            ? "," + btn.id
                            : btn.id;
                } else {
                    if (!getElement("addtagIDs").value.includes(btn.id))
                        getElement("addtagIDs").value += getElement("addtagIDs")
                            .value
                            ? "," + btn.id
                            : btn.id;
                }
                return true;
            },
            onDeselect: (btn) => {
                if (!btn.classList.contains("tag-name")) {
                    getElement("addtagIDs").value = getElement("addtagIDs")
                        .value.replaceAll(btn.id, "")
                        .split(",")
                        .filter((x) => x)
                        .join(",");
                } else {
                    getElement("addtags").value = getElement("addtags")
                        .value.replaceAll(btn.id, "")
                        .split(",")
                        .filter((x) => x)
                        .join(",");
                }
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
        const data = await postRequest2({
            path: setUrlParams(URLS.TAGSEARCH, projectID),
            data: {
                query: e.target.value,
            }
        });
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
                buttons.push(
                    `<button type="button" class="${
                        getElement("addtags").value.includes(e.target.value)
                            ? "positive"
                            : "primary"
                    } tag-new tag-name" id="${e.target.value}">${Icon("add")}${
                        e.target.value
                    }</button>`
                );
                getElement("tags-viewer-new").innerHTML = buttons.join("");
                loadNewTags();
                loadExistingTags();
            }
        } else {
            error(data.error);
        }
    };
    loadExistingTags();
}
if (ismoderator || selfProject) {
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
            return;
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
        getElements("delete-snapshot").forEach((btn) => {
            btn.onclick = (e) => {
                alertify
                    .confirm(
                        "Delete snapshot",
                        "Are you sure you want to delete snapshot?",
                        () => {
                            postRequest2({
                                path:setUrlParams(
                                    URLS.SNAPSHOT,
                                    projectID,
                                    "remove"
                                ),
                                data:{
                                    snapid: btn.getAttribute("data-snapid"),
                                }
                            }).then((data) => {
                                if (data.code === code.OK) {
                                    btn.parentElement.remove();
                                    message(data.message);
                                } else {
                                    error(data.error);
                                }
                            });
                        },
                        () => {}
                    )
                    .set("labels", { ok: "Yes", cancel: "No" })
                    .set("closable", false);
            };
        });
    });
};

loadsnaps.click();

const loadLiveData = async () => {
    const contribview = getElement("project-contibutors-view");
    const languageview = getElement("project-languages-view");
    if (contribview) setHtmlContent(contribview, loaderHTML());
    if (languageview) setHtmlContent(languageview, loaderHTML());
    if (contribview || languageview) {
        const data = await getRequest(setUrlParams(URLS.LIVEDATA, projectID));
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
