let compdata = {};
let intv;

const loadData = async () => {
    const data = await postRequest2({
        path: setUrlParams(URLS.DATA, compID),
        retainCache: true,
    });
    if (data && data.code === code.OK) {
        compdata = { ...data };
        Object.freeze(compdata);
        clearInterval(intv);
        if (isActive) {
            let timeleft = data.timeleft;
            if (timeleft === 0) return;
            getElement("remainingTime").innerHTML = secsToTime(timeleft);
            intv = setInterval(() => {
                timeleft -= 1;
                if (timeleft < 0) {
                    clearInterval(intv);
                    subLoader();
                    loader();
                    window.location.replace(window.location.pathname);
                    return;
                }
                const disptime = secsToTime(timeleft);
                getElement("remainingTime").innerHTML = disptime;
                try {
                    getElement("finalTimeLeft").innerHTML = disptime;
                } catch {}
            }, 1000);
        } else {
            if (data.startTimeLeft > 0) {
                let timeleft = data.startTimeLeft;
                setInterval(() => {
                    timeleft -= 1;
                    if (timeleft < 0) {
                        clearInterval(intv);
                        subLoader();
                        window.location.replace(window.location.pathname);
                        return;
                    }
                }, 1000);
            }
        }
    }
};

try {
    loadData();
    getElement("remainingTime").innerHTML = loaderHTML();
    getElement("reload-time").onclick = (_) => {
        loadData();
    };
} catch {}

let taskinit = false;
const loadTabScript = (attr, tab) => {
    switch (attr) {
        case "task": {
            try{
                [getElement('compete-task-summary'),getElement('compete-task-detail'),getElement('compete-task-sample')].forEach(e=>{
                    let s = new SimpleMDE({
                        element: e,
                        toolbar: false,
                        status: false
                    });
                    s.togglePreview();
                    s.codemirror.options.readOnly = true;
                })
                taskinit = true;
            } catch {}
        } break;
        case "submission":
            {
                if (isActive) {
                    if (compdata.participated) {
                        getElements("remove-person").forEach((remove) => {
                            remove.onclick = (_) => {
                                Swal.fire({
                                    title: `Remove teammate`,
                                    html: `Are you sure you want to remove ${remove.dataset.name} from this competition?`,
                                    showDenyButton: true,
                                    showCancelButton: false,
                                    confirmButtonText: STRING.cancel,
                                    denyButtonText: "Yes, remove",
                                }).then(async (result) => {
                                    if (result.isDenied) {
                                        const data = await postRequest2({
                                            path: setUrlParams(
                                                URLS.REMOVEMEMBER,
                                                compdata.subID,
                                                remove.dataset.userid
                                            ),
                                        });
                                        if (!data) return;
                                        if (data.code === code.OK) {
                                            message(
                                                "Removed " + remove.dataset.name
                                            );
                                            return tab.click();
                                        }
                                        error(data.error);
                                    }
                                });
                            };
                        });
                        try {
                            getElement("invitepeople").onclick = async (_) => {
                                await Swal.fire({
                                    title: "Invite teammate",
                                    html: `
                                    <div class="w3-row">
                                        <h5>Type the email address or Github ID of the person to invite them to participate with you.</h5>
                                        <input class="wide" type="text" required placeholder="Email address or Github ID" id="dialoginviteeID" /><br/>
                                        <span class="negative-text w3-right" id="dialoginviteerr"></span>
                                    </div>
                                    `,
                                    showCancelButton: true,
                                    showConfirmButton: true,
                                    confirmButtonText: "Send Invitation",
                                    cancelButtonText: "Cancel",
                                    preConfirm: async () => {
                                        const userID = String(
                                            getElement("dialoginviteeID").value
                                        ).trim();
                                        if (!userID) {
                                            getElement(
                                                "dialoginviteerr"
                                            ).innerHTML =
                                                "Please enter a valid ID";
                                            return false;
                                        }
                                        return true;
                                    },
                                }).then(async (result) => {
                                    if (result.isConfirmed) {
                                        const userID = String(
                                            getElement("dialoginviteeID").value
                                        ).trim();
                                        if (!userID) {
                                            getElement(
                                                "dialoginviteerr"
                                            ).innerHTML =
                                                "Please enter a valid ID";
                                        }
                                        const data = await postRequest(
                                            setUrlParams(
                                                URLS.INVITE,
                                                compdata.subID
                                            ),
                                            { userID }
                                        );
                                        if (data.code === code.OK) {
                                            success(
                                                `Invitation email sent successfully to ${userID}`
                                            );
                                            tab.click();
                                        } else {
                                            error(data.error);
                                        }
                                    }
                                });
                            };
                          } catch{};
                         try {
                            getElement("finalsubmit").onclick = async (_) => {
                                await Swal.fire({
                                    title: "Final submission",
                                    html: `
                                    <div class="w3-row">
                                        <h3>Are you sure you want to <strong>submit</strong>?</h3>
                                        <h6>This action is <span class="negative-text">irreversible</span>, which means once you submit, you submit it permanently on behalf of everyone in your submission team.</h6>
                                        <h4>Everyone in your submission team will be notified.</h4>
                                        <strong>Time Left: <span id="finalTimeLeft">---</span></strong><br/><br/>
                                        <br/><br/>
                                    </div>
                                    `,
                                    showCancelButton: true,
                                    showConfirmButton: true,
                                    showDenyButton: true,
                                    confirmButtonText: "Verify submission",
                                    cancelButtonText: "No, not yet",
                                    denyButtonText: "Yes, submit now",
                                    focusConfirm: false,
                                }).then(async (result) => {
                                    if (result.isDismissed) {
                                        message("Not submitted yet");
                                    } else if (result.isConfirmed) {
                                        const suburl = getElement(
                                            "submissionurl"
                                        )
                                            .getAttribute("data-saved")
                                            .trim();
                                        if (!suburl) {
                                            error("No submission URL saved!");
                                            return;
                                        }
                                        miniWindow(suburl, "Submission");
                                        return false;
                                    } else if (result.isDenied) {
                                        const suburl = getElement(
                                            "submissionurl"
                                        )
                                            .getAttribute("data-saved")
                                            .trim();
                                        const nsuburl =
                                            getElement(
                                                "submissionurl"
                                            ).value.trim();
                                        if (!suburl) {
                                            error("No submission URL saved!");
                                            return;
                                        }
                                        if (suburl != nsuburl) {
                                            error(
                                                "Submission URL changed, save before submitting!"
                                            );
                                            return false;
                                        }
                                        const data = await postRequest(
                                            setUrlParams(
                                                URLS.SUBMIT,
                                                compID,
                                                compdata.subID
                                            )
                                        );
                                        if (data.code === code.OK) {
                                            success(data.message);
                                            tab.click();
                                        } else {
                                            error(data.error);
                                        }
                                    }
                                });
                            };
                        } catch {}
                        try {
                          getElement("submit-quick-project").onclick=_=> {
                           userFreeProjectsSelect(async(fprojID)=>{
                             const data = await postRequest2({
                                 path: setUrlParams(URLS.SAVE,compID,compdata.subID),
                                 data: { submissionfreeproject:fprojID }
                             });
                             if(data && data.code == CODE.OK){
                                return tab.click();
                             }
                             return error(data.error)
                            });
                          }
                        } catch {}
                        try {
                          getElement("remove-quick-project").onclick=async()=> {
                             const data = await postRequest2({
                                 path: setUrlParams(URLS.SAVE,compID,compdata.subID),
                                 data: { submissionfreeproject:"remove" }
                             });
                            if(data && data.code == CODE.OK){
                                return tab.click();
                             }
                            return error(data.error)
                          }
                        } catch {}
                    }
                } else {
                    try {
                        getElement("finalsubmit").onclick = async (_) => {
                            await Swal.fire({
                                title: '<span class="negative-text">Late submission</span>',
                                html: `
                                <div class="w3-row">
                                    <h3>Are you sure you want to <strong>submit</strong>?</h3>
                                    <h6>This action is <span class="negative-text">irreversible</span>, which means once you submit, you submit it permanently on behalf of everyone in your submission team.</h6>
                                    <h4>Everyone in your submission team will be notified.</h4>
                                    <strong class="negative-text">NOTE: This late submission will affect its judgement.</strong>
                                    <br/><br/>
                                </div>
                                `,
                                showCancelButton: true,
                                showConfirmButton: true,
                                showDenyButton: true,
                                confirmButtonText: "Verify submission",
                                cancelButtonText: "No, not yet (later)",
                                denyButtonText: "Yes, submit now (late)",
                                focusConfirm: false,
                            }).then(async (result) => {
                                if (result.isDismissed) {
                                    message("Not submitted yet");
                                } else if (result.isConfirmed) {
                                    const suburl = getElement("submissionurl")
                                        .getAttribute("data-saved")
                                        .trim();
                                    if (!suburl) {
                                        error("No submission URL saved!");
                                        return;
                                    }
                                    miniWindow(suburl, "Submission");
                                    return false;
                                } else if (result.isDenied) {
                                    const suburl = getElement("submissionurl")
                                        .getAttribute("data-saved")
                                        .trim();
                                    const nsuburl =
                                        getElement(
                                            "submissionurl"
                                        ).value.trim();
                                    if (!suburl) {
                                        error("No submission URL saved!");
                                        return;
                                    }
                                    if (suburl != nsuburl) {
                                        error(
                                            "Submission URL changed, save before submitting!"
                                        );
                                        return false;
                                    }
                                    const data = await postRequest(
                                        setUrlParams(
                                            URLS.SUBMIT,
                                            compID,
                                            compdata.subID
                                        )
                                    );
                                    if (data.code === code.OK) {
                                        success(data.message);
                                        tab.click();
                                    } else {
                                        error(data.error);
                                    }
                                }
                            });
                        };
                    } catch {}
                }
            }
            break;
        case "result": {
            getElements("result-points").forEach((points) => {
                const rank = Number(points.getAttribute("data-rank"));
                const resID = points.getAttribute("data-resultID");
                points.onclick = async () => {
                    const data = await postRequest(
                        setUrlParams(URLS.TOPIC_SCORES, resID)
                    );
                    if (!data) return;
                    if (data.code !== code.OK) {
                        return error(data.error);
                    }
                    let scores = "";
                    data.topics.forEach((topic) => {
                        scores += `<div class="w3-row pallete-slab" id='${resID}-${topic.id}'>
                            <h6>${topic.name}<span class="w3-right">${topic.score}</span></h6>
                        </div>
                        `;
                        topic.id, topic.name, topic.score;
                    });
                    Swal.fire({
                        title: `Rank Scorecard`,
                        html: `<h4>Rank ${numsuffix(
                            rank
                        )} points distribution</h4>${scores}`,
                    });
                };
            });
        }
    }
    try {
        getElement("finalsubmit").onclick = async (_) => {
            await Swal.fire({
                title: "Final submission",
                html: `
                <div class="w3-row">
                    <h3>Are you sure you want to <strong>submit</strong>?</h3>
                    <h6>This action is <span class="negative-text">irreversible</span>, which means once you submit, you submit it permanently on behalf of everyone in your submission team.</h6>
                    <h4>Everyone in your submission team will be notified.</h4>
                    <strong>Time Left: <span id="finalTimeLeft">---</span></strong><br/><br/>
                    <br/><br/>
                </div>
                `,
                showCancelButton: true,
                showConfirmButton: true,
                showDenyButton: true,
                confirmButtonText: "Verify submission",
                cancelButtonText: "Cancel",
                denyButtonText: "Final Submit",
                focusConfirm: false,
            }).then(async (result) => {
                if (result.isDismissed) {
                    message("Not submitted yet");
                } else if (result.isConfirmed) {
                    const suburl = getElement("submissionurl")
                        .getAttribute("data-saved")
                        .trim();
                    if (!suburl) {
                        error("No submission URL saved!");
                        return;
                    }
                    miniWindow(suburl, "Submission");
                    return false;
                } else if (result.isDenied) {
                    const suburl = getElement("submissionurl")
                        .getAttribute("data-saved")
                        .trim();
                    const nsuburl = getElement("submissionurl").value.trim();
                    if (!suburl) {
                        error("No submission URL saved!");
                        return;
                    }
                    if (suburl != nsuburl) {
                        error(
                            "Submission URL changed, save before submitting!"
                        );
                        return false;
                    }
                    const data = await postRequest(
                        setUrlParams(URLS.SUBMIT, compID, compdata.subID)
                    );
                    if (data.code === code.OK) {
                        success(data.message);
                        tab.click();
                    } else {
                        error(data.error);
                    }
                }
            });
        };
    } catch {}
    if (!taskinit && attr=='task'){
        [getElement('compete-task-summary'),getElement('compete-task-detail'),getElement('compete-task-sample')].forEach(e=>{
            let s = new SimpleMDE({
                element: e,
                toolbar: false,
                status: false
            });
            s.togglePreview();
            s.codemirror.options.readOnly = true;
        })
    }
};

initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(
            setUrlParams(
                URLS.COMPETETABSECTION,
                compID,
                tab.getAttribute("data-id")
            )
        ),
    uniqueID: "competetab",
    tabsClass: "side-nav-tab",
    activeTabClass: "active",
    onShowTab: (tab) => loadTabScript(tab.getAttribute("data-id"), tab),
    tabindex,
});
initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(
            setUrlParams(
                URLS.COMPETETABSECTION,
                compID,
                tab.getAttribute("data-id")
            )
        ),
    uniqueID: "competetabsmall",
    tabsClass: "side-nav-tab-small",
    activeTabClass: "active",
    onShowTab: (tab) => loadTabScript(tab.getAttribute("data-id"), tab),
    tabindex,
});
