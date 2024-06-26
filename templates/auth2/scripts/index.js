{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

const tabindex =
    Number("{{request.GET.tab}}" || -2) > -1
        ? Number("{{request.GET.tab}}")
        : false;
initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest2({
            path: setUrlParams(URLS.TAB_SECTION, tab.id),
        });
    },
    activeTabClass:
        "{{request.user.profile.theme}}" == "tertiary"
            ? "positive"
            : "{{request.user.profile.theme}}",
    inactiveTabClass:
        "{{request.user.profile.text_theme}}" == "positive-text"
            ? "primary {{request.user.profile.text_theme}}"
            : "primary text-primary",
    uniqueID: "authtab",
    tabindex,
    tabsClass: "auth-nav-tab",
    onShowTab: async (tab) => {
        switch (tab.id) {
            case "notification":
                {
                    let allcheck = false;
                    getElement("test-notification-action").onclick=async(_)=>{
                        await getRequest(URLS.NOTIF_ENABLED);
                        message('A notification has been sent to you to check if enabled.')
                    }
                    getElements("notification-toggle-email").forEach((tog) => {
                        tog.onclick = async (_) => {
                            const notifID = tog.getAttribute(
                                "data-notification-id"
                            );
                            const data = await postRequest2({
                                path: setUrlParams(
                                    URLS.NOTIFICATION_TOGGLE_EMAIL,
                                    notifID
                                ),
                                data: {
                                    subscribe: tog.checked,
                                },
                                retainCache: true,
                                silent: allcheck,
                            });
                            if (!(data && data.code == CODE.OK)) {
                                tog.checked = !tog.checked;
                                if (!allcheck) {
                                    if (data) error(data.error);
                                    else error();
                                }
                            }
                            getElement(
                                "notification-toggle-email-all"
                            ).checked = getElements(
                                "notification-toggle-email"
                            ).every((tog) => tog.checked);
                        };
                    });
                    getElements("notification-toggle-device").forEach((tog) => {
                        tog.onclick = async (_) => {
                            const notifID = tog.getAttribute(
                                "data-notification-id"
                            );
                            const notifname = tog.getAttribute(
                                "data-notification-name"
                            );
                            const method = async (done, err) => {
                                if (!done || err) {
                                    if (!allcheck) {
                                        message(
                                            tog.checked
                                                ? STRING.unable_to_sub_device_notif
                                                : STRING.unable_to_unsub_device_notif
                                        );
                                    }
                                    tog.checked = !tog.checked;
                                    getElement(
                                        "notification-toggle-device-all"
                                    ).checked = getElements(
                                        "notification-toggle-device"
                                    ).every((tog) => tog.checked);
                                    return;
                                }
                                const data = await postRequest2({
                                    path: setUrlParams(
                                        URLS.NOTIFICATION_TOGGLE_DEVICE,
                                        notifID
                                    ),
                                    data: {
                                        subscribe: tog.checked,
                                    },
                                    retainCache: true,
                                    silent: allcheck,
                                });
                                if (!(data && data.code == CODE.OK)) {
                                    tog.checked = !tog.checked;
                                    if (!allcheck) {
                                        if (data) error(data.error);
                                        else error();
                                    }
                                }
                                getElement(
                                    "notification-toggle-device-all"
                                ).checked = getElements(
                                    "notification-toggle-device"
                                ).every((tog) => tog.checked);
                            };
                            if (tog.checked) {
                                subscribeToPush(
                                    notifID,
                                    notifname,
                                    allcheck,
                                    method
                                );
                            } else {
                                unsubscribeFromPush(
                                    notifID,
                                    notifname,
                                    allcheck,
                                    method
                                );
                            }
                        };
                    });
                    getElement("notification-toggle-email-all").onclick = (
                        e
                    ) => {
                        getElements("notification-toggle-email").forEach(
                            (tog) => {
                                allcheck = true;
                                tog.checked = !e.target.checked;
                                tog.click();
                                allcheck = false;
                            }
                        );
                    };
                    getElement("notification-toggle-device-all").onclick = (
                        e
                    ) => {
                        getElements("notification-toggle-device").forEach(
                            (tog) => {
                                allcheck = true;
                                tog.checked = !e.target.checked;
                                tog.click();
                                allcheck = false;
                            }
                        );
                    };
                    getElement("notification-toggle-device-all").checked =
                        getElements("notification-toggle-device").every(
                            (tog) => tog.checked
                        );
                    getElement("notification-toggle-email-all").checked =
                        getElements("notification-toggle-email").every(
                            (tog) => tog.checked
                        );
                }
                break;
            case "security":
                {
                    const deactivationDialog = async () => {
                        await Swal.fire({
                            title: STRING.deactivate_appname_account,
                            html: `<h5>${STRING.you_sure_to} ${NegativeText(
                                STRING.de_activate
                            )} ${STRING.your_acc}?<br/>${
                                STRING.account_hidden_from_all
                            }<br/>${
                                STRING.deactive_profile_url_wont_work
                            }<br/>${STRING.can_reactivate_anytime}</h5>`,
                            showConfirmButton: false,
                            showDenyButton: true,
                            showCancelButton: true,
                            denyButtonText:
                                Icon("toggle_off") +
                                " " +
                                STRING.deactivate_my_acc,
                            cancelButtonText: STRING.no_go_back,
                        }).then(async (result) => {
                            if (result.isDenied) {
                                message(STRING.deactivating_acc);
                                loaders(true);
                                const data = await postRequest2({
                                    path: URLS.ACCOUNTACTIVATION,
                                    data: {
                                        deactivate: true,
                                    },
                                });
                                if (data && data.code === code.OK) {
                                    message(STRING.acc_deactivated);
                                    return await logOut();
                                }
                                loaders(false);
                                error(data.error);
                            }
                        });
                    };
                    getElement("deactivateaccount").onclick = async (_) => {
                        _reauthenticate(deactivationDialog);
                    };

                    const accountDeletionDialog = async () => {
                        let successorSet = false;
                        let successorID = "";
                        let useDefault = false;
                        loader();
                        let sdata = await postRequest2({
                            path: URLS.GETSUCCESSOR,
                        });
                        if (!sdata) return loader(sdata);
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
                            <h3>Your account will be deleted, and you'll lose all your data on ${APPNAME}, ${NegativeText(
                                    "permanently"
                                )}.</h3>
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
                        <button class="negative small" id="makesuccessor" ${
                            useDefault || successorSet ? "hidden" : ""
                        }>${Icon("schedule_send")}MAKE SUCCESSOR</button>
                        </div>
                        <div class="w3-col w3-quarter w3-center">
                        <label for="defaultsuccessor">
                            <input type="checkbox" id="defaultsuccessor" ${
                                useDefault ? "checked" : ""
                            } />
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
                                    const data = await postRequest2({
                                        path: URLS.ACCOUNTDELETE,
                                        data: {
                                            confirmed: true,
                                        },
                                    });
                                    if (data.code === code.OK) {
                                        return await logOut();
                                    }
                                    loaders(false);
                                    error("Failed to delete");
                                }
                            )
                            .set("closable", false)
                            .set("labels", {
                                ok: `Cancel (<span id="cancelDeletionDialogSecs">60</span>s)`,
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
                            let done = await postRequest2({
                                path: URLS.INVITESUCCESSOR,
                                data: {
                                    set: e.target.checked,
                                    unset: !e.target.checked,
                                    useDefault: e.target.checked,
                                },
                            });
                            if (done && done.code === code.OK) {
                                useDefault = e.target.checked;
                            } else {
                                error("An error occurred");
                                e.target.checked = !e.target.checked;
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
                            const successorID =
                                getElement("successorID").value.trim();
                            if (!successorID && !useDefault)
                                return error(
                                    "Successor email required, or set default successor."
                                );
                            const data = await postRequest2({
                                path: URLS.INVITESUCCESSOR,
                                data: {
                                    set: true,
                                    userID: successorID || false,
                                    useDefault,
                                },
                            });
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
                        let secs = 60;
                        let intv = setInterval(() => {
                            secs -= 1;
                            getElement("cancelDeletionDialogSecs").innerHTML =
                                secs;
                            if (secs === 0) {
                                clearInterval(intv);
                                dial.close();
                            }
                        }, 1000);
                    };

                    getElement("deleteaccount").onclick = (_) => {
                        _reauthenticate(accountDeletionDialog);
                    };

                    getElements("unblock-button").forEach((unblock) => {
                        const username = unblock.getAttribute("data-username");
                        const userID = unblock.getAttribute("data-userID");
                        unblock.onclick = (_) => {
                            Swal.fire({
                                title: `Un-block ${username}?`,
                                html: `<h6>Are you sure you want to ${PositiveText(
                                    `unblock ${username}`
                                )}? You both will be visible to each other on ${APPNAME}, including all associated activities.
                                    <br/>You can block them anytime from their profile.
                                </h6>`,
                                showCancelButton: true,
                                cancelButtonText: STRING.no_go_back,
                                confirmButtonText: `${Icon(
                                    "remove_circle_outline"
                                )} Unblock ${username}`,
                            }).then(async (res) => {
                                if (res.isConfirmed) {
                                    const data = await postRequest2({
                                        path: URLS.People.UNBLOCK_USER,
                                        data: { userID },
                                    });
                                    if (!data) return;
                                    if (data.code === code.OK) {
                                        message(`Unblocked ${username}.`);
                                        return tab.click();
                                    }
                                    error(data.error);
                                }
                            });
                        };
                    });
                }
                break;
            case 'account' :{
                getElement("nickname").oninput = async (e) => {
                    let nickname = String(e.target.value).toLowerCase().trim();
                    nickname = nickname.replace(/[^a-z0-9\-]/g, "-").split('-').filter((k)=>k.length).join('-');
                    if (!nickname) return;
                    e.target.value = nickname;
                };
                getElement("save-edit-nickname").onclick =
                        async () => {
                            const obj = getFormDataById(
                                "edit-nickname-form"
                            );
                            if(!obj.nickname)
                            {
                                error("Nickname cannot be empty")
                                return
                            }
                            const resp = await postRequest2({
                                path: setUrlParams(URLS.NICKNAMEEDIT),
                                data: {
                                    nickname: obj.nickname
                                },
                            });
                            if (resp.code === code.OK) 
                            {
                                success(STRING.nickname_updated)
                                return tab.click();
                            }
                            error(resp.error);
                            getElement("edit-nickname-button").click()
                            getElement("nickname").focus()
                        };
                const pauseModDialog = async () => {
                    if ("{{request.user.profile.mod_isPending}}"=="True")
                    {
                        await Swal.fire({
                            title: `${NegativeText("Can't Pause Moderation")}`,
                            html: `<h5>You have pending moderations. Please resolve them first</h5>`,
                            showConfirmButton: true,
                            showDenyButton: false,
                            showCancelButton: true,
                            cancelButtonText: "Go back",
                            confirmButtonText: "Take me to moderation tab",
                        }).then(async (result) => {
                            if (result.isConfirmed) {
                                relocate({path : "{{request.user.profile.getLink}}", query : {
                                    tab : 4,
                                    a : STRING.resolve_pending
                                }})
                            }
                        })
                        return
                    }
                    paused = getElement("paused").value
                    if(paused=="True")
                        paused = true
                    else
                        paused = false
                    const resp = await postRequest2({
                        path: setUrlParams(URLS.PAUSE_MODERATORSHIP),
                        data: {
                            paused: paused
                        },
                    });
                    if (resp.code === code.OK) 
                    {
                        if (paused)
                            success(STRING.moderation_paused)
                        else
                            success(STRING.moderation_resumed)
                        return tab.click();
                    }
                    error(resp.error);
                };
                const leaveModDialog = async () => {
                    if ("{{request.user.profile.mod_isPending}}"=="True")
                    {
                        await Swal.fire({
                            title: `${NegativeText("Can't Leave Moderation")}`,
                            html: `<h5>You have pending moderations. Please resolve them first</h5>`,
                            showConfirmButton: true,
                            showDenyButton: false,
                            showCancelButton: true,
                            cancelButtonText: "Go back",
                            confirmButtonText: "Take me to moderation tab",
                        }).then(async (result) => {
                            if (result.isConfirmed) {
                                relocate({path : "{{request.user.profile.getLink}}", query : {
                                    tab : 4,
                                    a : STRING.resolve_pending
                                }})
                            }
                        })
                        return
                    }
                    if("{{request.user.profile.mod_isApproved}}"=="True")
                    {
                        await Swal.fire({
                            title: `${NegativeText("Can't Leave Moderation")}`,
                            html: `<h5>You have approved moderations. You need to transfer them before leaving moderation.<br/><br/>Please enter moderator mail so that we can transfer your approved projects.<br/><br/>You can also click "Go back" and transfer projects individually.</h5>
                            <br/>
                            <input id="moderator_mail" type="email" placeholder="Moderator mail" maxlength="70" name="moderator"/>`,
                            showConfirmButton: true,
                            showDenyButton: false,
                            showCancelButton: true,
                            cancelButtonText: "Go back",
                            confirmButtonText: "Transfer Projects",
                            preConfirm:function(){
                                mail = document.getElementById('moderator_mail').value
                            }
                        }).then(async (result) => {
                            if (result.isConfirmed) {
                                const data = await postRequest2({
                                path: URLS.Projects.INVITE_LEAVE_MOD,
                                data: {
                                    email: mail,
                                },
                            });
                            if (data && data.code === code.OK) {
                                await Swal.fire({
                                    title: "Transfer Invite Sent",
                                    html: `<h5>Transfer invite has been sent and your moderation status has been paused. You moderation status will be revoked automatically if the invite get accepted otherwise you will have to transfer your projects to some other moderator.</h5>`,
                                    showConfirmButton: true,
                                    showDenyButton: false,
                                    showCancelButton: false,
                                    confirmButtonText: "Okay",
                                })
                                return
                            }
                            error(data.error);
                            }
                        })
                        return
                    }
                    await Swal.fire({
                        title: "Leave Moderation",
                        html: `<h5>${STRING.you_sure_to} ${NegativeText(
                            "leave"
                        )} Moderatorship?<br/>This action is irreversible. Proceed with caution.</h5>`,
                        showConfirmButton: false,
                        showDenyButton: true,
                        showCancelButton: true,
                        denyButtonText:
                            Icon("toggle_off") +
                            " " +
                            "Leave Moderatorship",
                        cancelButtonText: STRING.no_go_back,
                    }).then(async (result) => {
                        if (result.isDenied) {
                            message("Leaving Moderation");
                            const data = await getRequest2({
                                path: URLS.LEAVE_MODERATORSHIP
                            });
                            if (data && data.code === code.OK) {
                                relocate({query : {
                                    s : STRING.leave_moderation
                                }})
                                return
                            }
                            error(data.error);
                        }
                    });
                };
                getElement("pausemod").onclick = async (_) => {
                    pauseModDialog();
                };
                // getElement("leavemod").onclick = async (_) => {
                //     leaveModDialog();
                // };
            }
            break;
        }
    },
});

