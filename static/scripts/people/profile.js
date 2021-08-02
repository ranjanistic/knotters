const loadTabScript = (tab) => {
    switch (tab.id) {
        case "overview":
            {
                getElements("chart-view").forEach(async (chart) => {
                    const myChart = new Chart(chart.getContext("2d"), {
                        type: chart.getAttribute("data-type"),
                        data: {
                            labels: [
                                "Jan",
                            ],
                            datasets: [
                                {
                                    label: "Project activity",
                                    data: [0],
                                    backgroundColor: ["rgba(255, 99, 132, 1)"],
                                    borderColor: ["rgba(255, 99, 132, 1)"],
                                    borderWidth: 1,
                                },
                                {
                                    label: "Competition activity",
                                    data: [0],
                                    backgroundColor: ["rgba(255, 159, 64, 1)"],
                                    borderColor: ["rgba(255, 99, 132, 1)"],
                                    borderWidth: 1,
                                },
                            ],
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: false,
                                },
                            },
                        },
                    });
                });
                let lastquery = ''
                getElement("topic-search-input").oninput=async(e)=>{
                    if(e.target.value.length != lastquery.length){
                        if(e.target.value.length < lastquery.length){
                            lastquery=e.target.value
                            return
                        } else {
                            lastquery=e.target.value
                        }
                    }
                    getElement('topics-viewer-new').innerHTML = ''
                    const data = await postRequest(URLS.TOPICSEARCH, {
                        query:e.target.value,
                    })
                    if(!data) return
                    if (data.code===code.OK){
                        let buttons = []
                        data.topics.forEach((topic)=>{
                            buttons.push(`<button type="button" class="primary dead-text topic-choice topic-new" id="${topic.id}">${Icon('add')}${topic.name}</button>`)
                        })
                        if(buttons.length){
                            getElement('topics-viewer-new').innerHTML = buttons.join('')
                        } else {
                            getElement('topics-viewer-new').innerHTML = `No topics for '${e.target.value}'`
                        }
                    } else {
                        error(data.error)
                    }
                }
            }
            break;
        case "account":
            {
                const deactivationDialog = () => {
                    const ddial = alertify
                        .confirm(
                            `
                    <h4 class="negative-text">
                    Deactivate your ${APPNAME} account?
                    </h4>`,
                            `<h5>
                        Are you sure you want to ${NegativeText(
                            "de-activate"
                        )} your account?<br/>
                        Your account will NOT get deleted, instead, it will be hidden from everyone.

                        This also implies that your profile URL will not work during this period of deactivation.

                        You can reactivate your account by logging in again anytime.
                    </h5>`,
                            () => {},
                            async () => {
                                message("Deactivating account...");
                                loaders(true);
                                const data = await postRequest(
                                    URLS.ACCOUNTACTIVATION,
                                    {
                                        deactivate: true,
                                    }
                                );
                                if (data && data.code === code.OK) {
                                    message(
                                        "Your account has been deactivated."
                                    );
                                    return await logOut();
                                }
                                loaders(false);
                                error(data.error);
                            }
                        )
                        .set("labels", {
                            ok: "No, Go back",
                            cancel: `${Icon(
                                "toggle_off"
                            )} Deactivate my account`,
                        }).set('closable',false);
                };

                getElement("deactivateaccount").onclick = (_) => {
                    deactivationDialog();
                };

                const accountDeletionDialog = async () => {
                    let successorSet = false;
                    let successorID = "";
                    let useDefault = false;
                    loader();
                    let sdata = await postRequest(URLS.GETSUCCESSOR);
                    if(!sdata) return loader(sdata);
                    if (sdata.code === code.OK) {
                        successorSet = true;
                        successorID = sdata.successorID;
                        if (!successorID) useDefault = true;
                    }
                    loader(false);
                    const dial = alertify
                        .confirm(
                            `<h4>${NegativeText("Account Deletion")}</h4>`,
                            `<br/><br/>
                    
                        <h1 class="negative-text">Deleting your account is a permanent action!</h1>
                        <h3>Your account will be deleted, and you'll lose all your data on ${APPNAME}, ${NegativeText('permanently')}.</h3>
                        <h5>
                        By default, your profile assets will be transferred to and controlled by our <a class="positive-text" href="/people/profile/knottersbot">knottersbot</a>.<br/><br/>
                        If you want to specify your own successor to which all your active assets will be transferred, type their email address below,
                        they will receive an email to accept or decline your successor invite.<br/>If declined, then the default successor will be set.
                        </h5>
                        <br/>
                    <br/>

                    <strong>You can deactivate your account instead, if you want a break. This way you won't lose your account.</strong><br/><br/>
                    <button class="accent" id="deactivateaccount1">${Icon(
                        "toggle_off"
                    )}Deactivate Account</button><br/><br/>

                    <div class="w3-col w3-half">
                    <input type="email" required ${
                        successorSet ? "disabled" : ""
                    } class="wide" id="successorID" placeholder="Your successor's email address" value="${
                                useDefault
                                    ? "Using default successor"
                                    : successorID
                            }"/>
                    <br/>
                    <br/>
                    <button class="negative small" id="makesuccessor" ${useDefault || successorSet ? "hidden" : ""}>${Icon("schedule_send")}MAKE SUCCESSOR</button>
                    </div>
                    <div class="w3-col w3-quarter w3-center">
                    <label for="defaultsuccessor">
                        <input type="checkbox" id="defaultsuccessor" ${useDefault ? "checked" : ""} />
                        <span class="w3-large">Use default successor</span>
                    </label>
                    <br/><br/><br/>
                    </div>
                    `,
                            () => {
                                message("We thought we lost you!");
                                clearInterval(intv);
                                dial.close();
                            },
                            async () => {
                                clearInterval(intv);
                                if (!successorSet) {
                                    return error(
                                        "Successor email required, or set default successor."
                                    );
                                }
                                message("Preparing for deletion");
                                loaders();
                                const data = await postRequest(
                                    URLS.ACCOUNTDELETE,
                                    {
                                        confirmed: true,
                                    }
                                );
                                if (data.code === code.OK) {
                                    return await logOut();
                                }
                                loaders(false);
                                error("Failed to delete");
                            }
                        )
                        .set("closable", false)
                        .set("labels", {
                            ok: `Cancel (<span id="cancelDeletionDialogSecs">100</span>s)`,
                            cancel: `${Icon(
                                "delete_forever"
                            )}DELETE MY ACCOUNT (no tricks)`,
                        })
                        .set("modal", true)
                        .maximize();

                    getElement("deactivateaccount1").onclick = (_) => {
                        clearInterval(intv);
                        dial.close();
                        deactivationDialog();
                    };

                    getElement("defaultsuccessor").onchange = async (e) => {
                        let done = await postRequest(
                            URLS.INVITESUCCESSOR,
                            {
                                set: e.target.checked,
                                unset: !e.target.checked,
                                useDefault:e.target.checked,
                            }
                        );
                        if (done && done.code === code.OK) {
                            useDefault = e.target.checked;
                        } else {
                            error('An error occurred');
                            e.target.checked = !e.target.checked
                        }
                        successorSet = useDefault;
                        visibleElement("makesuccessor", !useDefault);
                        getElement("successorID").disabled = useDefault;
                        getElement("successorID").value = useDefault
                            ? "Using default successor"
                            : "";
                    };
                    getElement("makesuccessor").onclick = async () => {
                        let useDefault = defaultsuccessor.checked;
                        const successorID = getElement(
                            "successorID"
                        ).value.trim();
                        if (!successorID && !useDefault)
                            return error(
                                "Successor email required, or set default successor."
                            );
                        const data = await postRequest(
                            URLS.INVITESUCCESSOR,
                            {
                                set: true,
                                userID: successorID || false,
                                useDefault,
                            }
                        );
                        if (data && data.code === code.OK) {
                            successorSet = true;
                            hideElement("makesuccessor");
                            getElement("successorID").value = useDefault
                                ? "Using default successor"
                                : successorID;
                            getElement("successorID").disabled = true;
                            message(`Successor set.`);
                        } else {
                            error(data.error);
                        }
                    };
                    let secs = 100;
                    let intv = setInterval(() => {
                        secs -= 1;
                        getElement("cancelDeletionDialogSecs").innerHTML = secs;
                        if (secs === 0) {
                            clearInterval(intv);
                            dial.close();
                        }
                    }, 1000);
                };

                getElement("deleteaccount").onclick = (_) => {
                    accountDeletionDialog();
                };
            }
            break;
        default:
            break;
    }
};

initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest(setUrlParams(URLS.PROFILETAB,userID,tab.id));
    },
    uniqueID: "profiletab",
    onShowTab: loadTabScript,
});

if (selfProfile) {
    initializeTabsView({
        onEachTab: async (tab) => {
            return await getRequest(setUrlParams(URLS.SETTINGTAB,tab.id));
        },
        uniqueID: "profilestab",
        tabsClass: "set-tab",
        activeTabClass: "active",
        inactiveTabClass: "primary",
        viewID: "stabview",
        spinnerID: "sloader",
        onShowTab: loadTabScript,
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
