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
                                loader(true);
                                subLoader(true);
                                const data = await postRequest(
                                    `${ROOT}/account/activation`,
                                    {
                                        deactivate: true,
                                    }
                                );
                                if (data.code === code.OK) {
                                    message(
                                        "Your account has been deactivated."
                                    );
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
                            )} Deactivate my account`,
                        });
                };

                getElement("deactivateaccount").onclick = (_) => {
                    deactivationDialog();
                };

                const accountDeletionDialog = () => {
                    let successorSet = false
                    const dial = alertify
                        .confirm(
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
                    <label for="defaultsuccessor">
                    Use default successor
                    <input type="checkbox" id="defaultsuccessor"/>
                    </label>
                    <button class="negative small" id="makesuccessor">${Icon(
                        "schedule_send"
                    )}MAKE SUCCESSOR</button>`,
                            async () => {
                                if(!successorSet) return error("Successor email required, or set default successor.")
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
                            }
                        )
                        .set("labels", {
                            cancel: "Cancel",
                            ok: `${Icon(
                                "delete_forever"
                            )}DELETE MY ACCOUNT (no tricks)`,
                        }, 'modal', true)
                        .maximize();

                    getElement("deactivateaccount1").onclick = (_) => {
                        dial.close()
                        deactivationDialog();
                    };
                    getElement("makesuccessor").onclick = async () => {
                        const useDefault = defaultsuccessor.checked
                        const successorID = getElement(
                            "successorID"
                        ).value.trim();
                        if (!successorID && !useDefault)
                            return error(
                                "Successor email required, or set default successor."
                            );
                        subLoader(true);
                        const data = await postRequest(
                            `${ROOT}/profile/successor/invite`,
                            {
                                set: true,
                                userID:successorID||false,
                                useDefault
                            }
                        );
                        subLoader(false);
                        if (data.code === code.OK) {
                            successorSet = true
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
