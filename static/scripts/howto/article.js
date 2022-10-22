if (self){
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

                getElement("removetagIDs").value = getElement(
                    "removetagIDs"
                )
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
                        getElement("addtagIDs").value += getElement(
                            "addtagIDs"
                        ).value
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
            path: setUrlParams(URLS.SEARCH_TAGS, articleID),
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
                    } tag-new tag-name" id="${e.target.value}">${Icon(
                        "add"
                    )}${e.target.value}</button>`
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

    getElement("save-edit-articletags").onclick = async () => {
        var obj = getFormDataById("edit-tag-inputs");
        var resp = await postRequest(
            setUrlParams(URLS.EDIT_TAGS, articleID),
            {
                addtagIDs: obj.addtagIDs.split(",").filter((str) => str),
                addtags: obj.addtags.split(",").filter((str) => str),
                removetagIDs: obj.removetagIDs
                    .split(",")
                    .filter((str) => str),
            }
        );
        if (resp.code === code.OK) {
            subLoader();
            return window.location.reload();
        }
        error(resp.error);
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
                    3
                ) {
                    error(STRING.upto_3_topics_allowed);
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
                        3
                ) {
                    error(STRING.upto_3_topics_allowed);
                    return false;
                }
                if (btn.classList.contains("topic-name")) {
                    if (!getElement("addtopics").value.includes(btn.id))
                        getElement("addtopics").value += getElement(
                            "addtopics"
                        ).value
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
                    getElement("addtopicIDs").value = getElement(
                        "addtopicIDs"
                    )
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
            path: setUrlParams(URLS.SEARCH_TOPICS, articleID),
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
                getElement("topics-viewer-new").innerHTML =
                    buttons.join("");
                loadNewTopics();
                loadExistingTopics();
            } else {
                buttons.push(
                    `<button type="button" class="${
                        getElement("addtopics").value.includes(
                            e.target.value
                        )
                            ? "positive"
                            : "primary"
                    } topic-new topic-name" id="${e.target.value}">${Icon(
                        "add"
                    )}${e.target.value}</button>`
                );
                getElement("topics-viewer-new").innerHTML =
                    buttons.join("");
                loadNewTopics();
                loadExistingTopics();
            }
        } else {
            error(data.error);
        }
    };
    loadExistingTopics();
    getElement("save-edit-articletopics").onclick = async () => {
        const obj = getFormDataById("edit-article-topics-form");
        const resp = await postRequest2({
            path: setUrlParams(URLS.EDIT_TOPICS, articleID),
            data: {
                addtopicIDs: obj.addtopicIDs.split(",").filter((x) => x),
                addtopics: obj.addtopics.split(",").filter((x) => x),
                removetopicIDs: obj.removetopicIDs
                    .split(",")
                    .filter((x) => x),
            },
        });
        if (resp.code === code.OK) {
            subLoader();
            return window.location.reload();
        }
        error(resp.error);
    };
}