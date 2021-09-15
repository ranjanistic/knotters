let compdata = {};
let intv;

const loadData = async () => {
    const data = await postRequest(setUrlParams(URLS.DATA, compID));
    if (data.code === code.OK) {
        compdata = { ...data };
        Object.freeze(compdata);
        clearInterval(intv);
        if (isActive) {
            let timeleft = data.timeleft;
            if (timeleft === 0) return;
            getElement("remainingTime").innerHTML = secsToTime(timeleft);
            intv = setInterval(() => {
                timeleft -= 1;
                if (timeleft<0) {
                    clearInterval(intv);
                    subLoader();
                    loader();
                    window.location.replace(window.location.pathname);
                    return
                }
                const disptime = secsToTime(timeleft);
                getElement("remainingTime").innerHTML = disptime;
                try {
                    getElement("finalTimeLeft").innerHTML = disptime;
                } catch {}
            }, 1000);
        } else {
            if(data.startTimeLeft>0){
                let timeleft = data.startTimeLeft;
                setInterval(() => {
                    timeleft -= 1;
                    if (timeleft<0) {
                        clearInterval(intv);
                        subLoader();
                        window.location.replace(window.location.pathname);
                        return
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

const loadTabScript = (attr) => {
    switch (attr) {
        case "submission": {
            if (isActive) {
                if (compdata.participated) {
                    getElements("remove-person").forEach((remove) => {
                        remove.onclick = (_) => {
                            alertify
                                .alert(
                                    `Remove teammate`,
                                    `
                            <div class="w3-row">
                                <h4>Are you sure you want to <span class="negative-text">remove</span> 
                                ${remove.getAttribute("data-name")}?</h4>
                                <form method="POST" action="${setUrlParams(
                                    URLS.REMOVEMEMBER,
                                    compdata.subID,
                                    remove.getAttribute("data-userID")
                                )}">
                                    ${csrfHiddenInput(csrfmiddlewaretoken)}
                                    <button class="negative">Yes, remove</button>
                                </form>
                            </div>`
                                )
                                .set({ label: "Cancel" });
                        };
                    });
                    try {
                        getElement("invitepeople").onclick = (_) => {
                            const inviteDialog = alertify
                                .alert(
                                    `Invite teammate`,
                                    `
                            <div class="w3-row">
                                <h5>Type the email address or Github ID of the person to invite them to participate with you.</h5>
                                <input class="wide" type="text" required placeholder="Email address or Github ID" id="dialoginviteeID" /><br/>
                                <span class="negative-text w3-right" id="dialoginviteerr"></span>
                                <br/>
                                <button class="active" id="dialoginvite">Invite</button>
                                <button class="positive" id="sharecompetition">${Icon('share')}Share competition</button>
                            </div>`
                                )
                                .set({ label: "Cancel" });
                            getElement("dialoginviteerr").innerHTML = "";
                            getElement('sharecompetition').onclick=_=>{
                                shareLinkAction(`Competition at ${APPNAME}`, `Checkout this competition at ${APPNAME}, let's participate together. Hurry up! Time is not our friend.\n`, setUrlParams(URLS.COMPID, compID),()=>{
                                    message(`Invite them from here after they finish signing up on ${APPNAME}.`)
                                })
                            }
                            getElement("dialoginvite").onclick = async () => {
                                const userID = String(
                                    getElement("dialoginviteeID").value
                                ).trim();
                                const data = await postRequest(
                                    setUrlParams(URLS.INVITE, compdata.subID),
                                    { userID }
                                );
                                if (data.code === code.OK) {
                                    inviteDialog.close();
                                    alertify.success(
                                        `Invitation email sent successfully to ${userID}`
                                    );
                                    tab.click();
                                } else {
                                    getElement("dialoginviteerr").innerHTML =
                                        data.error;
                                }
                            };
                        };
                        getElement("finalsubmit").onclick = (_) => {
                            const submitDialog = alertify
                                .confirm(
                                    `<h4>Final submission</h4>`,
                                    `
                                <div class="w3-row">
                                    <h3>Are you sure you want to <strong>submit</strong>?</h3>
                                    <h6>This action is <span class="negative-text">irreversible</span>, which means once you submit, you submit it permanently on behalf of everyone in your submission team.</h6>
                                    <h4>Everyone in your submission team will be notified.</h4>
                                    <strong>Time Left: <span id="finalTimeLeft">---</span></strong><br/><br/>
                                    <button onclick="miniWindow('${
                                        getElement("submissionurl").value
                                    }', 'Submission')" class="positive">${Icon(
                                        "open_in_new"
                                    )}Verify submission</button>
                                    <br/><br/>
                                </div>`,
                                    async () => {
                                        const data = await postRequest(
                                            setUrlParams(
                                                URLS.SUBMIT,
                                                compID,
                                                compdata.subID
                                            )
                                        );
                                        if (data.code === code.OK) {
                                            alertify.success(data.message);
                                            submitDialog.close();
                                            tab.click();
                                        } else {
                                            alertify.error(data.error);
                                        }
                                    },
                                    () => {
                                        submitDialog.close();
                                    }
                                )
                                .set("labels", {
                                    ok: "Yes, submit now",
                                    cancel: "No, wait!",
                                });
                        };
                    } catch {}
                }
            } else {
                try {
                    getElement("finalsubmit").onclick = (_) => {
                        const lateSubmitDialog = alertify
                            .confirm(
                                `<h4 class="negative-text">Late submission</h4>`,
                                `
                                <div class="w3-row">
                                    <h3>Are you sure you want to submit?</h3>
                                    <h6>This action is <span class="negative-text">irreversible</span>, which means once you submit, you submit it permanently on behalf of everyone in your submission team.</h6>
                                    <strong class="negative-text">NOTE: This late submission will affect its judgement.</strong>
                                    <br/><br/>
                                    <button onclick="miniWindow('${
                                        getElement("submissionurl").value
                                    }', 'Submission')" class="positive">${Icon(
                                    "open_in_new"
                                )}Verify submission</button>
                                </div>`,
                                async () => {
                                    const data = await postRequest(
                                        setUrlParams(
                                            URLS.SUBMIT,
                                            compID,
                                            compdata.subID
                                        )
                                    );
                                    if (data.code === code.OK) {
                                        alertify.success(data.message);
                                        lateSubmitDialog.close();
                                        tab.click();
                                    } else {
                                        alertify.error(data.error);
                                    }
                                },
                                () => {
                                    lateSubmitDialog.close();
                                }
                            )
                            .set("labels", {
                                ok: "Yes, submit now (Late)",
                                cancel: "No, not yet (Later)",
                            });
                    };
                } catch {}
            }
        }
    }
};

initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(setUrlParams(URLS.COMPETETABSECTION, compID, tab.getAttribute('data-id'))),
    uniqueID: "competetab",
    tabsClass: "side-nav-tab",
    activeTabClass: "active",
    onShowTab: loadTabScript,
    tabindex
});
initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(setUrlParams(URLS.COMPETETABSECTION, compID, tab.getAttribute('data-id'))),
    uniqueID: "competetabsmall",
    tabsClass: "side-nav-tab-small",
    activeTabClass: "active",
    onShowTab:(tab)=> loadTabScript(tab.getAttribute('data-id')),
    tabindex
});
