if (selfProject || ismoderator) {
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
                    error(STRING.upto_5_topics_allowed);
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
                    error(STRING.upto_5_topics_allowed);
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
            data: {
                query: e.target.value,
            },
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
            path: setUrlParams(URLS.TOPICSUPDATE, projectID),
            data: {
                addtopicIDs: obj.addtopicIDs.split(",").filter((x) => x),
                addtopics: obj.addtopics.split(",").filter((x) => x),
                removetopicIDs: obj.removetopicIDs.split(",").filter((x) => x),
            },
        });
        if (resp.code === code.OK) {
            subLoader();
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
                    error(STRING.upto_5_tags_allowed);
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
                    error(STRING.upto_5_tags_allowed);
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
            },
        });
        if (!data) return;
        if (data.code === code.OK) {
            let buttons = [];
            data.tags.forEach((tag) => {
                buttons.push(
                    `<button type="button" class="small ${
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
                    `<button type="button" class="small ${
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
    getElements("delete-assets-action").forEach(async (action) => {
        action.onclick = async () => {
            const assetID = action.getAttribute("data-assetid");
            const data = await postRequest2({
                path: setUrlParams(URLS.MANAGE_ASSETS, projectID),
                data: {
                    action: ACTIONS.REMOVE,
                    assetID
                },
                retainCache: true,
            });
            if (!data) return;
            if (data.code === code.OK) {
                message("Asset deleted.");
                if (getElements("delete-assets-action").length > 1) {
                    getElement(`asset-view-${assetID}`).remove();
                } else {
                    refresh({});
                }
                return;
            }
            error(data.error);
        };
    });
    getElements("visibility-assets-action").forEach(async (action) => {
        action.onclick = async () => {
            const makepublic = action.getAttribute("data-public") != "1";
            const data = await postRequest2({
                path: setUrlParams(URLS.MANAGE_ASSETS, projectID),
                data: {
                    action: ACTIONS.UPDATE,
                    assetID: action.getAttribute("data-assetid"),
                    public: makepublic,
                },
                retainCache: true,
            });
            if (!data) return;
            if (data.code === code.OK) {
                message(`Asset is ${makepublic ? "public" : "private"} now.`);
                action.setAttribute("data-public", makepublic ? "1" : "0");
                action.classList.remove(
                    makepublic ? "active-text" : "positive-text"
                );
                action.classList.add(
                    makepublic ? "positive-text" : "active-text"
                );
                action.innerHTML = makepublic ? "lock_open" : "lock";
                action.title = makepublic ? `${APPNAME} community can access`:"Only you can access";
                return true;
            }
            error(data.error);
        };
    });
    getElements("add-assets-action").forEach(async (action) => {
        action.onclick = (_) => {
            let filedata = {
                action: ACTIONS.CREATE,
                filedata: null,
                filename: null,
                actualFilename: null,
                public: false,
            };
            Swal.fire({
                title: "Add project asset",
                html: `
                    <input type="text" placeholder="Asset name" maxlength="100" id="asset-name" />
                    <br/>
                    <br/>
                    <input type="file" id="asset-file" class="wide" />
                    <br/>
                    <input type="checkbox" id="asset-public" placeholder="Public" />
                    <label for="asset-public">Public</label><br/>
                    <strong class="negative-text" id="asset-error"></strong>
                `,
                showConfirmButton: true,
                showCancelButton: true,
                confirmButtonText: STRING.confirm,
                allowOutsideClick: false,
                didOpen: async () => {
                    getElement("asset-file").onchange = async (e) => {
                        const file = e.target.files[0];
                        if (file.size / 1024 / 1024 > 10) {
                            error(STRING.file_too_large_10M);
                            return;
                        }
                        filedata.filedata = await convertFileToBase64(file);
                        filedata.actualFilename = file.name;
                    };
                },
                preConfirm: () => {
                    let filename = getElement("asset-name").value.trim();
                    if (!filename) {
                        getElement("asset-error").innerHTML =
                            STRING.asset_name_required;
                        return false;
                    }
                    filedata.filename = filename;
                    if (!filedata.filedata) {
                        getElement("asset-error").innerHTML =
                            STRING.asset_file_required;
                        return false;
                    }
                    filedata.public = getElement("asset-public").checked;
                },
            }).then(async (result) => {
                if (result.isConfirmed) {
                    if (!filedata.filedata || !filedata.filename) return;
                    const data = await postRequest2({
                        path: setUrlParams(URLS.MANAGE_ASSETS, projectID),
                        data: filedata,
                        retainCache: true,
                    });
                    if (!data) return;
                    if (data.code === code.OK) {
                        futureMessage("Asset added successfully");
                        return refresh({});
                    }
                    error(data.error);
                }
            });
        };
    });
}

let snapstart = 0,
    snapend = snapstart + 2;
let excludeProjectSnapIDs = [];
const snapsview = getElement(`snapshots-view`);

const loadsnaps = getElement("load-more-snaps");

loadsnaps.onclick = (_) => {
    postRequest2({
        path: setUrlQueries(setUrlParams(URLS.SNAPSHOTS, projectID, 5), {
            n: excludeProjectSnapIDs[excludeProjectSnapIDs.length - 1] || 0,
        }),
        data: {
            excludeIDs: excludeProjectSnapIDs,
        },
        allowCache: true,
        retainCache: true,
    }).then((data) => {
        if (!data || data.code !== CODE.OK) {
            return error(data ? data.error : "");
        }
        let newdiv = document.createElement("div");
        newdiv.classList.add("w3-row");
        snapsview.appendChild(newdiv);
        if (
            !data.snapIDs.length ||
            data.snapIDs.some((id) => excludeProjectSnapIDs.includes(id))
        ) {
            setHtmlContent(
                newdiv,
                `<div class="dead-text" align="center"><br/>${STRING.no_more_snaps}</div>`
            );
            return hide(loadsnaps);
        }
        setHtmlContent(newdiv, data.html, loadSnapshotActions);
        show(loadsnaps);
        excludeProjectSnapIDs = excludeProjectSnapIDs.concat(data.snapIDs);
    });
};

loadsnaps.click();

const loadLiveData = async () => {
    const languageview = getElement("project-languages-view");
    const contribview = getElement("project-contibutors-view");
    const commitsview = getElement("project-commits-view");
    const langdefaulthtml = languageview ? languageview.innerHTML : "";
    const contribDefhtml = contribview ? contribview.innerHTML : "";
    const commitsDefhtml = commitsview ? commitsview.innerHTML : "";
    if (contribview) setHtmlContent(contribview, loaderHTML());
    if (languageview) setHtmlContent(languageview, loaderHTML());
    if (commitsview) setHtmlContent(commitsview, loaderHTML());
    if (contribview || languageview || commitsview) {
        const data = await getRequest(setUrlParams(URLS.LIVEDATA, projectID));
        if (!data || data.code !== code.OK) {
            if (languageview) {
                setHtmlContent(
                    languageview,
                    loadErrorHTML(`livelangdataretry`)
                );
                getElement(`livelangdataretry`).onclick = (_) => loadLiveData();
            }
            if (commitsview) {
                setHtmlContent(
                    commitsview,
                    loadErrorHTML(`livecommitdataretry`)
                );
                getElement(`livecommitdataretry`).onclick = (_) =>
                    loadLiveData();
            }
            if (contribview) {
                setHtmlContent(contribview, loadErrorHTML(`livecontdataretry`));
                getElement(`livecontdataretry`).onclick = (_) => loadLiveData();
            }
            return;
        }
        if (contribview) {
            if (data.contributorsHTML)
                setHtmlContent(contribview, data.contributorsHTML);
            else setHtmlContent(contribview, contribDefhtml);
        }
        if (commitsview) {
            if (data.commitsHTML) setHtmlContent(commitsview, data.commitsHTML);
            else setHtmlContent(commitsview, commitsDefhtml);
        }
        if (languageview) {
            if (Object.keys(data.languages).length) {
                setHtmlContent(
                    languageview,
                    `<canvas id="project-languages-distribution-chart" class="chart-view" data-type="radar" width="400" height="400"></canvas>`
                );
                radarChartView(
                    getElement("project-languages-distribution-chart"),
                    Object.keys(data.languages),
                    Object.keys(data.languages).map(
                        (key) => data.languages[key]
                    ),
                    projectcolor
                );
            } else {
                setHtmlContent(languageview, langdefaulthtml);
            }
        }
    }
};
try {
    loadLiveData();
} catch (e) {
    console.debug(e);
}
