const loadTabScript = (tab) => {
    switch (tab.id) {
        case "overview":
            {
                getElements("chart-view").forEach(async (chart) => {
                    radarChartView(
                        chart,
                        getElements("topic-name").map((top) => top.innerHTML),
                        getElements("topic-points")
                            .map((top) => Number(top.innerHTML))
                            .every((p) => p === 0)
                            ? []
                            : getElements("topic-points").map((top) =>
                                  Number(top.innerHTML)
                              ),
                        isMentor
                            ? COLOR.active()
                            : isModerator
                            ? COLOR.accent()
                            : COLOR.positive()
                    );
                });
                if (selfProfile) {
                    const loadExistingTopics = () => {
                        initializeMultiSelector({
                            candidateClass: "topic-existing",
                            selectedClass: "negative",
                            deselectedClass: "primary negative-text",
                            onSelect: (btn) => {
                                const remtopIDselem =
                                    getElement("removetopicIDs");
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
                                let addtoplen =
                                    addtopids.length + addtops.length;

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
                                let addtoplen =
                                    addtopids.length + addtops.length;

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
                                    if (
                                        !getElement("addtopics").value.includes(
                                            btn.id
                                        )
                                    )
                                        getElement("addtopics").value +=
                                            getElement("addtopics").value
                                                ? "," + btn.id
                                                : btn.id;
                                } else {
                                    if (
                                        !getElement(
                                            "addtopicIDs"
                                        ).value.includes(btn.id)
                                    )
                                        getElement("addtopicIDs").value +=
                                            getElement("addtopicIDs").value
                                                ? "," + btn.id
                                                : btn.id;
                                }
                                return true;
                            },
                            onDeselect: (btn) => {
                                if (!btn.classList.contains("topic-name")) {
                                    getElement("addtopicIDs").value =
                                        getElement("addtopicIDs")
                                            .value.replaceAll(btn.id, "")
                                            .split(",")
                                            .filter((x) => x)
                                            .join(",");
                                } else {
                                    getElement("addtopics").value = getElement(
                                        "addtopics"
                                    )
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
                            path: URLS.TOPICSEARCH,
                            data: {
                                query: e.target.value,
                            },
                            retainCache: true,
                            allowCache: true,
                        });
                        if (!data) return;
                        if (data.code === code.OK) {
                            let buttons = [];
                            data.topics.forEach((topic) => {
                                buttons.push(
                                    `<button type="button" class="${
                                        getElement(
                                            "addtopicIDs"
                                        ).value.includes(topic.id)
                                            ? "positive"
                                            : "primary"
                                    } topic-new" id="${topic.id}">${Icon(
                                        "add"
                                    )}${topic.name}</button>`
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
                                    } topic-new topic-name" id="${
                                        e.target.value
                                    }">${Icon("add")}${e.target.value}</button>`
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
                    getElement("save-edit-profiletopics").onclick =
                        async () => {
                            const obj = getFormDataById(
                                "edit-profile-topics-form"
                            );
                            const resp = await postRequest2({
                                path: setUrlParams(URLS.TOPICSUPDATE),
                                data: {
                                    addtopicIDs: obj.addtopicIDs
                                        .split(",")
                                        .filter((x) => x),
                                    addtopics: obj.addtopics
                                        .split(",")
                                        .filter((x) => x),
                                    removetopicIDs: obj.removetopicIDs
                                        .split(",")
                                        .filter((x) => x),
                                },
                                retainCache: true,
                            });
                            if (resp.code === code.OK) return tab.click();
                            error(resp.error);
                        };
                }
            }
            break;
        
        case "people": {
            if (isManager && selfProfile) {
                getElement("send-mgm-invite").onclick = async () => {
                    Swal.fire({
                        title: "Invite person",
                        html: `<h6>Invite a person to your organization as a member.<br/>
                        Type their email to send invitation right away.</h6>
                        <br/>
                        <input class="wide" type="email" autocomplete="email" placeholder="New email address" id="mgm-person-new-email" />
                        `,
                        showCancelButton: true,
                        confirmButtonText: "Send Invite",
                        cancelButtonText: "Cancel",
                        showLoaderOnConfirm: true,
                        preConfirm: async () => {
                            let email = getElement(
                                "mgm-person-new-email"
                            ).value.trim();
                            if (email) return email;
                            error("Email address required");
                            return false;
                        },
                    }).then(async (result) => {
                        if (result.isConfirmed) {
                            message("Sending invitation...");
                            const data = await postRequest2({
                                path: URLS.Management.PEOPLE_MGM_SEND_INVITE,
                                data: {
                                    action: "create",
                                    email: result.value,
                                },
                                retainCache: true,
                            });
                            if (data.code === code.OK) {
                                message("Invitation sent.");
                                return tab.click();
                            }
                            error(data.error);
                        }
                    });
                };

                getElements("delete-mgm-person-invite").forEach((del) => {
                    del.onclick = (_) => {
                        Swal.fire({
                            title: "Delete Invitation",
                            imageUrl: del.getAttribute("data-receiver-dp"),
                            imageWidth: 90,
                            html: `<h6>Delete invitation for ${del.getAttribute(
                                "data-receiver-name"
                            )}?</h6>`,
                            showCancelButton: true,
                            confirmButtonText: "Delete",
                            cancelButtonText: "No",
                        }).then(async (result) => {
                            if (result.isConfirmed) {
                                message("Deleting invitation...");
                                const data = await postRequest2({
                                    path: URLS.Management
                                        .PEOPLE_MGM_SEND_INVITE,
                                    data: {
                                        action: "remove",
                                        inviteID:
                                            del.getAttribute("data-inviteID"),
                                    },
                                    retainCache: true,
                                });
                                if (data.code === code.OK) {
                                    message("Invitation deleted.");
                                    return tab.click();
                                }
                                error(data.error);
                            }
                        });
                    };
                });
            }
            getElements("delete-mgm-person").forEach((del) => {
                del.onclick = (_) => {
                    Swal.fire({
                        title: "Remove Member",
                        imageUrl: del.getAttribute("data-member-dp"),
                        imageWidth: 90,
                        html: `<h6>Remove member ${del.getAttribute(
                            "data-member-name"
                        )}?</h6>`,
                        showCancelButton: true,
                        confirmButtonText: "Remove",
                        cancelButtonText: "No",
                    }).then(async (result) => {
                        if (result.isConfirmed) {
                            message("Removing member...");
                            const data = await postRequest2({
                                path: URLS.Management.PEOPLE_MGM_REMOVE,
                                data: {
                                    userID: del.getAttribute("data-userID"),
                                    mgmID,
                                },
                                retainCache: true,
                            });
                            if (data.code === code.OK) {
                                message("Member removed.");
                                return tab.click();
                            }
                            error(data.error);
                        }
                    });
                };
            });
        }
        default:
            break;
    }
};

initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest2({
            path: setUrlParams(URLS.PROFILETAB, userID, tab.id),
        });
    },
    uniqueID: "profiletab",
    onShowTab: loadTabScript,
    activeTabClass: isMentor ? "active" : isModerator ? "accent" : "positive",
    tabindex,
    inactiveTabClass:
        "primary " +
        (isMentor
            ? "text-primary"
            : isModerator
            ? "text-primary"
            : "positive-text"),
});

if (selfProfile) {
    initializeTabsView({
        onEachTab: async (tab) => {
            return await getRequest(setUrlParams(URLS.SETTINGTAB, tab.id));
        },
        uniqueID: "profilestab",
        tabsClass: "set-tab",
        activeTabClass: isMentor
            ? "active"
            : isModerator
            ? "accent"
            : "positive",
        inactiveTabClass:
            "primary " +
            (isMentor
                ? "text-primary"
                : isModerator
                ? "text-primary"
                : "positive-text"),
        viewID: "stabview",
        spinnerID: "sloader",
        onShowTab: loadTabScript,
        tabindex,
    });

    getElement("uploadprofilepic").onchange = (e) => {
        handleCropImageUpload(
            e,
            "profileImageData",
            "profilePicOutput",
            (croppedB64) => {
                getElement("uploadprofilepiclabel").innerHTML = "Selected";
                getElement("profilePicOutput").style.opacity = 1;
            }
        );
    };
}
