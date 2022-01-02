const loadBrowseSnaps = async (excludeIDs = []) => {
    const viewers = getElements("snapshot-viewer");
    let viewer = viewers.find((view) => view.innerHTML.trim() == "");
    if (!viewer) {
        viewer = viewers[viewers.length - 1];
    }
    const snapdata = await postRequest2({
        path: setUrlParams(URLS.BROWSER, BROWSE.PROJECT_SNAPSHOTS),
        data: { excludeIDs },
        retainCache: true,
        allowCache: true,
    });
    if (!snapdata) return false;
    if (snapdata.code === code.OK && snapdata.snapIDs.length) {
        setHtmlContent(viewer, viewer.innerHTML + snapdata.html);
        return snapdata.snapIDs;
    }
    return false;
};

const loadSnapshotScroller = async () => {
    const viewers = getElements("snapshot-viewer");
    if (viewers.length) {
        let viewedSnaps = [];
        let done = await loadBrowseSnaps();
        if (done) {
            viewedSnaps = viewedSnaps.concat(done);
            let options = {
                root: null,
                rootMargins: "0px",
                threshold: 0.5,
            };
            const observer = new IntersectionObserver(async (entries) => {
                if (entries[0].isIntersecting && done) {
                    viewedSnaps = viewedSnaps.concat(done);
                    done = await loadBrowseSnaps(viewedSnaps);
                }
            }, options);
            observer.observe(
                document.querySelector(
                    `#snap-${viewedSnaps[viewedSnaps.length - 1].replaceAll(
                        "-",
                        ""
                    )}`
                )
            );
        }
    }
};
const showSnapshotMoreBtn = (snapID) => {
    getElement(`snap-modal-${snapID}`).style.display = "flex";
    setTimeout(() => {
        getElement(`snap-laptop-${snapID}`).classList.add("right-snap");
        getElement(`snap-mob-${snapID}`).classList.add("bottom-snap");
    }, 50);
};
const closeSnapshotMoreBtn = (snapID, event) => {
    const snapmodal = getElement(`snap-modal-${snapID}`);
    if (event.target == snapmodal) {
        getElement(`snap-laptop-${snapID}`).classList.remove("right-snap");
        getElement(`snap-mob-${snapID}`).classList.remove("bottom-snap");
        setTimeout(() => {
            snapmodal.style.display = "none";
        });
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
};

const reportSnap = async (snapID) =>
    await violationReportDialog(
        URLS.Projects ? URLS.Projects.REPORT_SNAPSHOT : URLS.REPORT_SNAPSHOT,
        { snapID },
        "Snapshot",
        URLS.Projects ? URLS.Projects.REPORT_CATEGORIES : URLS.REPORT_CATEGORIES
    );

const deleteSnap = (snapID, projectID) => {
    if (!snapID || !projectID) return;
    Swal.fire({
        title: `Delete snapshot`,
        html: `Are you sure you want to delete the snapshot?`,
        showDenyButton: true,
        denyButtonText: "Yes, delete",
        confirmButtonText: "No, wait!",
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
                    hideElement(`snap-${snapID}`);
                    message(data.message);
                    closeSnapshotMoreBtn(snapID, {
                        target: getElement(`snap-modal-${snapID}`),
                    });
                } else {
                    error(data.error);
                }
            });
        }
    });
};
