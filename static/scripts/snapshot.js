const snapshotExcludeIDS = [];
const loadBrowseSnaps = async () => {
    const viewers = getElements("snapshot-viewer-parent");
    let viewer = viewers.find((view) => view.innerHTML.trim() == "");
    if (!viewer) {
        viewer = viewers[viewers.length - 1];
    }
    const snapdata = await postRequest2({
        path: setUrlQueries(
            setUrlParams(URLS.BROWSER, BROWSE.PROJECT_SNAPSHOTS),
            { n: snapshotExcludeIDS[snapshotExcludeIDS.length - 1] || 0 }
        ),
        data: { excludeIDs: snapshotExcludeIDS },
        retainCache: true,
        allowCache: true,
        silent: true,
    });
    if (!snapdata) return false;
    if (snapdata.code === code.OK && snapdata.snapIDs.length) {
        if (snapshotExcludeIDS.some((id) => snapdata.snapIDs.includes(id))) {
            return false;
        }
        let newdiv = document.createElement("div");
        newdiv.classList.add("align", "snapshot-viewer", "w3-row");
        viewer.appendChild(newdiv);
        setHtmlContent(newdiv, snapdata.html, loadSnapshotActions);
        snapshotExcludeIDS.push(...snapdata.snapIDs);
        return true;
    }
    return false;
};

const loadSnapshotActions = () => {
    getElements("snapshot-admire-action").forEach((admire) => {
        admire.onclick = (_) => {
            console.log("yes", admire.getAttribute("data-snaplink"));
            if (AUTHENTICATED) {
                admireSnap(admire.getAttribute("data-snapid"));
            } else {
                refer({
                    path: URLS.Auth.LOGIN,
                    query: {
                        next: admire.getAttribute("data-snaplink"),
                    },
                });
            }
        };
    });
    getElements("snapshot-admire-count-action").forEach((action) => {
        action.onclick = (_) => {
            showSnapAdmirers(action.getAttribute("data-snapid"));
        };
    });
    getElements("snapshot-more-action").forEach((action) => {
        const snapID = action.getAttribute("data-snapid");
        const projectID = action.getAttribute("data-snap-projectID");
        const snapLink = action.getAttribute("data-snaplink");
        const selfSnap = action.getAttribute("data-selfsnap") == "1";
        console.log(selfSnap);
        action.onclick = (_) => {
            showSnapshotMoreBtn(snapID, projectID, snapLink, selfSnap);
        };
    });
};

const loadSnapshotScroller = async () => {
    const viewers = getElements("snapshot-viewer-parent");
    if (viewers.length) {
        let done = await loadBrowseSnaps();
        if (done) {
            const observer = new IntersectionObserver(
                async (entries) => {
                    if (entries[0].isIntersecting && done) {
                        done = await loadBrowseSnaps();

                        if (done) {
                            observer.observe(
                                document.querySelector(
                                    `#snap-${snapshotExcludeIDS[
                                        Math.floor(
                                            snapshotExcludeIDS.length / 2
                                        )
                                    ].replaceAll("-", "")}`
                                )
                            );
                        } else {
                            if (navigator.onLine) {
                                observer.unobserve(
                                    document.querySelector(
                                        `#snap-${snapshotExcludeIDS[
                                            Math.floor(
                                                snapshotExcludeIDS.length / 2
                                            )
                                        ].replaceAll("-", "")}`
                                    )
                                );
                            }
                        }
                    }
                },
                {
                    root: null,
                    rootMargins: "0px",
                    threshold: 0,
                }
            );
            observer.observe(
                document.querySelector(
                    `#snap-${snapshotExcludeIDS[
                        Math.floor(snapshotExcludeIDS.length / 2)
                    ].replaceAll("-", "")}`
                )
            );
        }
    }
};

const showSnapshotMoreBtn = (snapID, projectID, snapLink, selfSnap = false) => {
    getElement("snap-modal").style.display = "flex";
    setTimeout(() => {
        getElement("snap-laptop").classList.add("right-snap");
        getElement("snap-mob").classList.add("bottom-snap");
    }, 40);
    getElement("snap-modal").onclick = (e) => closeSnapshotMoreBtn(e, snapID);
    getElements("delete-snapshot-action").forEach((act) => {
        if (selfSnap) {
            console.log("delete", snapID);
            show(act);
            act.onclick = () => deleteSnap(snapID, projectID);
        } else {
            hide(act);
        }
    });
    getElements("report-snapshot-action").forEach((act) => {
        if (!selfSnap) {
            console.log("report", snapID);
            show(act);
            act.onclick = () => reportSnap(snapID);
        } else {
            hide(act);
        }
    });
    if (!AUTHENTICATED) {
        getElements("login-snapshot-action").forEach((act) => {
            act.onclick = () =>
                refer({
                    path: URLS.Auth.LOGIN,
                    query: {
                        next: snapLink,
                    },
                });
        });
    }
    getElement(`snap-${snapID}`).style.zIndex = "900";
};

const closeSnapshotMoreBtn = (event, snapID) => {
    const snapmodal = getElement("snap-modal");
    if (event.target == snapmodal) {
        getElement("snap-laptop").classList.remove("right-snap");
        getElement("snap-mob").classList.remove("bottom-snap");
        setTimeout(() => {
            snapmodal.style.display = "none";
        });
        getElement("snap-modal").onclick = null;
        getElements("delete-snapshot-action").forEach((act) => {
            act.onclick = null;
        });
        getElements("report-snapshot-action").forEach((act) => {
            act.onclick = null;
        });
        getElements("login-snapshot-action").forEach((act) => {
            act.onclick = null;
        });
        getElement(`snap-${snapID}`).style.zIndex = "1";
    }
};

const admireSnap = async (snapID) => {
    if (!snapID) return;
    const admire =
        getElement(`snap-admire-${snapID}`).getAttribute("data-admires") == "0";
    const data = await postRequest2({
        path: setUrlParams(
            URLS.Projects
                ? URLS.Projects.TOGGLE_SNAP_ADMIRATION
                : URLS.TOGGLE_SNAP_ADMIRATION,
            snapID
        ),
        data: {
            admire,
        },
        retainCache: true,
    });
    if (data.code !== code.OK) {
        return error(data.error);
    }
    getElement(`snap-admire-${snapID}`).setAttribute(
        "data-admires",
        admire ? 1 : 0
    );
    getElement(`snap-admire-${snapID}`).classList[admire ? "add" : "remove"](
        "positive"
    );
    getElement(`snap-admire-${snapID}`).classList[admire ? "remove" : "add"](
        "primary"
    );
    getElement(`snap-admirecount-${snapID}`).innerHTML =
        Number(getElement(`snap-admirecount-${snapID}`).innerHTML) +
        (admire ? 1 : -1);
};

const reportSnap = async (snapID) =>
    await violationReportDialog(
        URLS.Projects ? URLS.Projects.REPORT_SNAPSHOT : URLS.REPORT_SNAPSHOT,
        { snapID },
        STRING.snapshot,
        URLS.Projects ? URLS.Projects.REPORT_CATEGORIES : URLS.REPORT_CATEGORIES
    );

const deleteSnap = (snapID, projectID, afterDel = null) => {
    if (!snapID || !projectID) return;
    Swal.fire({
        title: `${STRING.delete} ${STRING.snapshot}`,
        html: `<h5>${STRING.you_sure_to} ${STRING.delete_the_snap}?</h5>`,
        showDenyButton: true,
        denyButtonText: STRING.yes_del,
        confirmButtonText: STRING.no_wait,
    }).then((res) => {
        if (res.isDenied) {
            postRequest2({
                path: setUrlParams(
                    URLS.Projects ? URLS.Projects.SNAPSHOT : URLS.SNAPSHOT,
                    projectID,
                    "remove"
                ),
                data: {
                    snapid: snapID,
                    snapID,
                },
                retainCache: true,
            }).then((data) => {
                if (data.code === code.OK) {
                    if (afterDel) {
                        afterDel();
                    } else {
                        hideElement(`snap-${snapID}`);
                        closeSnapshotMoreBtn(
                            {
                                target: getElement("snap-modal"),
                            },
                            snapID
                        );
                    }
                    message(data.message);
                } else {
                    error(data.error);
                }
            });
        }
    });
};

const showSnapAdmirers = async (snapID) => {
    Swal.fire({
        html: await getRequest2({
            path: setUrlParams(URLS.Projects.SNAP_ADMIRATIONS, snapID),
        }),
        title: "<h4 class='positive-text'>Admirers</h4>",
    });
};
