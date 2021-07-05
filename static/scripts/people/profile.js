const accountDeletionDialog = () => {
    
    alertify.confirm(
        `<h4 class="negative-text">Account Deletion</h4>`,
        `<br/><h6>We can let you delete your account, but your projects, if any, will have to be transferred to you successor.<br/>
    By default, your projects will be transferred to and controlled by our <a class="positive-text" href="/people/profile/knottersbot">knottersbot</a>.<br/><br/>
    However, if you want to specify your own successor on ${APPNAME}, to which all your projects will be transferred, type their email address below.<br/><br/>
    Your chosen successor will receive an email with choice to confirm this or not under 10 days. Till then, your account will not be deleted, but deactivated.<br/><br/>
    If you login again during this period, then your account will be reactivated and deletion will be cancelled (successor will also not get appointed).<br/><br/>
    If your successor accepts this transfer, then your account will be deleted instantly.<br/><br/>
    If your successor declines this transfer, then knottersbot will become your successor.<br/><br/>
    If you don't appoint a successor, then knottersbot will become your successor and your account will be deleted in 24 hours, unless you login again in the same duration.<br/>
    </h6><br/>
    <strong>You can deactivate your account instead, if you want a break.</strong><br/><br/>
    <button class="accent" id="deactivateaccount1">${Icon(
        "toggle_off"
    )}Deactivate Account</button><br/><br/>
    <input type="email" class="wide" id="successorID" placeholder="Your successor's email address" />
    <button class="negative small" id="makesuccessor">${Icon(
        "schedule_send"
    )}MAKE SUCCESSOR</button>`,
        async () => {
            message("Preparing for deletion");
            loader(true);
            subLoader(true);
            const data = await postRequest(
                `${ROOT}/account/delete`,
                {
                    confirmed: true,
                }
            );
            if (data.code === code.OK) {
                logOut();
            }
        },
        () => {
            message("We thought we lost you!");
        },
    )
    .set("labels", {
        cancel: "Cancel",
        ok: `${Icon(
            "delete_forever"
        )}DELETE MY ACCOUNT (no tricks)`,
    }).maximize()
    

getElement("deactivateaccount1").onclick = (_) => {
    deactivationDialog();
};
getElement("makesuccessor").onclick = async () => {
    const successorID = getElement(
        "successorID"
    ).value.trim();
    if (!successorID)
        return error(
            "Successor email required, or delete account without your successor."
        );
    subLoader(true);
    const data = await postRequest(
        `${ROOT}/account/successor`,
        {
            successorID,
        }
    );
    subLoader(false);
    if (data.code === code.OK) {
        hideElement("makesuccessor");
        getElement("successorID").value = successorID;
        getElement("successorID").disabled = true;
        message(`Successor appointed.`);
    } else {
        subLoader(false);
        error(data.error);
    }
};    
};


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
                                "Feb",
                                "Mar",
                                "Apr",
                                "May",
                                "Jun",
                                "Jul",
                                "Aug",
                                "Sep",
                                "Oct",
                                "Nov",
                                "Dec",
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
                                    beginAtZero: true,
                                },
                            },
                        },
                    });
                });
            }
            break;
        case "account":
            {
                const deactivationDialog = () => {
                    const ddial = alertify
                        .confirm(
                            `
                    <h4 class="negative-text">
                    Deactivate your ${APPNAME} Account?
                    </h4>`,
                            `<h5>
                        Are you sure you want to ${NegativeText(
                            "de-activate"
                        )} your account?<br/>
                        Your account profile will NOT get deleted, instead, it will be hidden from everyone here, unless you login again.
                        This also implies that your profile url will not work during this period of deactivation.
                    </h5>`,
                            () => {},
                            async () => {
                                message("Deactivating account...");
                                loader(true);
                                subLoader(true);
                                let data = postRequest(
                                    `${ROOT}/account/deactivate`,
                                    {
                                        confirmed: true,
                                    }
                                );
                                if (data.code === code.OK) {
                                    return await logOut();
                                }
                                loader(false);
                                subLoader(false);
                                error(data.error);
                            }
                        )
                        .set("labels", {
                            ok: "No, Go back",
                            cancel: `${Icon(
                                "toggle_off"
                            )} Yes, deactivate my account`,
                        });
                };
                getElement("deactivateaccount").onclick = (_) => {
                    deactivationDialog();
                };

                
                getElement("deleteaccount").onclick = (_) => {
                    const dial = alertify
                        .confirm(
                            `<h4 class="negative-text">
                                Delete Your ${APPNAME} Account?
                            </h4>`,
                            `<h5>
                                Are you sure you want to ${NegativeText("delete")} your account permanently?
                            </h5>`,
                            ()=>{
                                dial.close()
                                window.dispatchEvent(new Event('deleteaccount'))
                            },
                            ()=>{

                            }
                        )
                        .set("labels", {
                            cancel: "No! Go back!",
                            ok: `${Icon(
                                "dangerous"
                            )} Yes, delete my account`,
                        });
                };
            }
            break;
        default:
            break;
    }
};

window.addEventListener('deleteaccount',()=>{
    accountDeletionDialog()
})

initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest(`${ROOT}/profiletab/${userID}/${tab.id}`);
    },
    uniqueID: "profiletab",
    onShowTab: loadTabScript,
});

if (selfProfile) {
    initializeTabsView({
        onEachTab: async (tab) => {
            return await getRequest(`${ROOT}/settingtab/${tab.id}`);
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
