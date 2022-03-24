{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

const ismoderator = "{{ismoderator}}" === "True";
const allsubsMarked =
    "{{moderation.competition.allSubmissionsMarked}}" === "True";
const resolved = "{{moderation.resolved}}" === "True";

if (allsubsMarked) {
} else if (!ismoderator) {
    let finalData = [];
    const localStorageKey =
        "{{moderation.getID}}{{moderation.type}}{{request.user.getID}}finalData";
    const eachTopicMaxPoint = Number(
        "{{moderation.competition.eachTopicMaxPoint}}"
    );
    const totalSubmissions = Number(
        "{{moderation.competition.totalValidSubmissions}}"
    );
    const totalTopics = Number("{{moderation.competition.totalTopics}}");
    const previous = window.localStorage.getItem(localStorageKey);
    if (previous) {
        try {
            finalData = JSON.parse(previous);
            finalData.forEach((psub) => {
                psub.topics.forEach((ptopic) => {
                    getElement(`${psub.subID}${ptopic.topicID}`).value =
                        ptopic.points;
                    getElement(
                        `${psub.subID}${ptopic.topicID}`
                    ).disabled = true;
                });
            });
        } catch {}
    }

    getElements("clear-subpoints").forEach((clear) => {
        const subID = String(clear.getAttribute("data-subID")).trim();
        clear.onclick = (_) => {
            finalData = finalData.filter((fd) => fd.subID != subID);
            getElements(`point-input-${subID}`).forEach((input) => {
                input.disabled = false;
                input.value = "";
            });
            window.localStorage.setItem(
                localStorageKey,
                JSON.stringify(finalData)
            );
        };
    });

    getElements("save-subpoints").forEach((save) => {
        const subID = String(save.getAttribute("data-subID")).trim();
        save.onclick = (_) => {
            finalData = finalData.filter((fd) => fd.subID != subID);
            finalData.push({
                subID,
                topics: [],
            });
            let added = false;
            finalData.some((fd, f) => {
                if (fd.subID == subID) {
                    getElements(`point-input-${subID}`).every((input) => {
                        if (input.value === "" || isNaN(input.value)) {
                            input.value = "";
                            error(`Point value cannot be empty.`);
                            input.focus();
                            return false;
                        }
                        if (
                            Number(input.value) > eachTopicMaxPoint ||
                            Number(input.value) < 0
                        ) {
                            error(
                                `Points shoud be <=${eachTopicMaxPoint} and >=0.`
                            );
                            input.focus();
                            return false;
                        }
                        input.disabled = true;
                        const topicID = input.getAttribute("data-topicID");
                        finalData[f].topics = finalData[f].topics.filter(
                            (topic) => topic.id != topicID
                        );
                        finalData[f].topics.push({
                            topicID,
                            points: Number(input.value),
                        });
                        added = true;
                        return true;
                    });
                    return true;
                }
                return false;
            });
            if (!added) {
                finalData.pop();
            }
            window.localStorage.setItem(
                localStorageKey,
                JSON.stringify(finalData)
            );
        };
    });

    getElement("finalsend").onclick = (_) => {
        if (!finalData.length) {
            error(
                '{% trans "No submissions marked." %} {% trans "Mark all submissions to send for ranking." %}'
            );
            getElements("topic-point").forEach((input) => {
                input.disabled = false;
            });
            return false;
        }
        if (finalData.length !== totalSubmissions) {
            getElements("topic-point").some((input) => {
                if (
                    !input.disabled ||
                    input.value === "" ||
                    isNaN(input.value) ||
                    !finalData.find(
                        (sub) => sub.subID == input.getAttribute("data-subID")
                    )
                ) {
                    error(
                        '{% trans "Please re-fill and save this input." %}'
                    );
                    input.disabled = false;
                    input.focus();
                    return true;
                }
            });
            return false;
        }

        if (
            !finalData.every((sub) => {
                if (sub.topics.length !== totalTopics) {
                    console.log(sub.subID);
                    console.log(
                        "yess",
                        getElement(`point-input-${sub.subID}`),
                        getElements(`point-input-${sub.subID}`)
                    );
                    getElements(`point-input-${sub.subID}`).some((input) => {
                        console.log(
                            "some",
                            sub.topics.some(
                                (topic) =>
                                    topic.topicID ===
                                    input.getAttribute("data-topicID")
                            )
                        );
                        if (
                            !input.disabled ||
                            input.value === "" ||
                            isNaN(input.value) ||
                            sub.topics.some(
                                (topic) =>
                                    topic.topicID ===
                                    input.getAttribute("data-topicID")
                            )
                        ) {
                            input.disabled = false;
                            input.focus();
                            error(
                                '{% trans "Please re-fill and save this input." %}'
                            );
                            return true;
                        }
                    });
                    return false;
                }
                if (
                    sub.topics.some((topic) => {
                        if (
                            Number(
                                getElement(`${sub.subID}${topic.topicID}`).value
                            ) !== topic.points
                        ) {
                            getElement(
                                `${sub.subID}${topic.topicID}`
                            ).disabled = false;
                            getElement(`${sub.subID}${topic.topicID}`).focus();
                            error(
                                '{% trans "Please re-fill and save this input." %}'
                            );
                            return true;
                        }
                        return false;
                    })
                ) {
                    return false;
                }
                return true;
            })
        ) {
            return false;
        }

        alertify
            .confirm(
                `{% trans "Send for ranking" %}?`,
                `<h4>{% trans "Are you sure you want to send all marked submissions for final ranking?" %}
            <br/>
            This action is <span class="negative-text">{% trans "irreversible" %}</span>.
        </h4>
        <h6>{% trans "Make sure that every submission is marked properly, as it will determine their final rank results." %}</h6>
        `,

                async () => {
                    message('{% trans "Sending for ranking" %}...');
                    loader(true);
                    subLoader(true);
                    const data = await postRequest(
                        "{{moderation.competition.submissionPointsLink}}",
                        {
                            submissions: finalData,
                        }
                    );
                    if (data.code === code.OK) {
                        success(
                            '{% trans "Submissions marked" %} & {% trans "submitted for ranking" %}.'
                        );
                        window.location.reload();
                    } else {
                        loader(false);
                        subLoader(false);
                        error(data.error);
                    }
                },
                () => {}
            )
            .set("labels", {
                ok: `${Icon(
                    "send"
                )}{% trans "Yes" %}, {% trans "send all" %}`,
                cancel: '{% trans "No" %}, {% trans "wait" %}!',
            });
    };

    getElement("discardall").onclick = (_) => {
        alertify
            .confirm(
                `{% trans "Discard changes" %}?`,
                `<h4>{% trans "Are you sure to discard all changes you made?" %} {% trans "All marked submissions will be unmarked, and you'll have to start again" %}!</h4>`,
                () => {},
                () => {
                    subLoader();
                    window.localStorage.removeItem(localStorageKey);
                    window.location.reload();
                }
            )
            .set("labels", {
                ok: `No, wait!`,
                cancel: `${Icon("delete")}Yes, discard`,
            });
    };
} else {
    const localStorageKey =
        "{{moderation.getID}}{{moderation.type}}{{request.user.getID}}finalData";
    let allsubmissionchecks = getElements("selectsubmission");
    let selectedAll = false;

    if (Number("{{moderation.competition.totalValidSubmissions}}") > 0 && !resolved) {
        let finalData = [];
        getElement("selectall").onclick = (_) => {
            allsubmissionchecks.forEach((checkbox) => {
                checkbox.checked = !selectedAll;
                getElement("selectall").innerHTML = selectedAll
                    ? `${Icon("check_box")} {% trans "Select All" %}`
                    : `${Icon(
                          "check_box_outline_blank"
                      )} {% trans "Deselect All" %}`;
            });
            selectedAll = !selectedAll;
        };

        getElement("approveselected").onclick = (_) => {
            if (!allsubmissionchecks.some((checkbox) => checkbox.checked))
                return error("No submission selected");
            let data = allsubmissionchecks.map((checkbox) => ({
                subID: String(checkbox.getAttribute("data-subID")).trim(),
                valid: checkbox.checked,
            }));
            const bulkDialog = alertify
                .confirm(
                    `{% trans "Confirm bulk operation" %}?`,
                    `<h4>Confirm to <span class="positive-text">approve ${
                        data.filter((sub) => sub.valid).length
                    }</span> submssions and 
                <span class="negative-text">reject ${
                    data.filter((sub) => !sub.valid).length
                }</span> submissions?</h4>
                `,
                    () => {
                        message(`Filtering...`);
                        data.forEach((d) => {
                            finalData = finalData.filter(
                                (fd) => fd.subID != d.subID
                            );
                            finalData.push(d);
                            if (!d.valid) {
                                allsubmissionchecks =
                                    allsubmissionchecks.filter(
                                        (checkbox) =>
                                            checkbox.id != `select${d.subID}`
                                    );
                                hide(getElement(`subslab${d.subID}`));
                            }
                        });
                        window.localStorage.setItem(
                            localStorageKey,
                            JSON.stringify(finalData)
                        );
                        message(`Filtered`);
                    },
                    () => bulkDialog.close()
                )
                .set("labels", {
                    ok: '{% trans "Yes" %}, {% trans "confirm" %}',
                    cancel: '{% trans "No" %}, {% trans "wait" %}!',
                });
        };

        getElement("rejectselected").onclick = (_) => {
            if (!allsubmissionchecks.some((checkbox) => checkbox.checked))
                return error("No submission selected");
            let data = allsubmissionchecks.map((checkbox) => ({
                subID: String(checkbox.getAttribute("data-subID")).trim(),
                valid: !checkbox.checked,
            }));
            const bulkDialog = alertify
                .confirm(
                    `{% trans "Confirm bulk operation" %}?`,
                    `<h4>Confirm to <span class="negative-text">reject ${
                        data.filter((sub) => !sub.valid).length
                    }</span> submssions and 
                <span class="positive-text">approve ${
                    data.filter((sub) => sub.valid).length
                }</span> submissions?</h4>
                `,
                    () => {
                        message(`{% trans "Filtering" %}...`);

                        data.forEach((d) => {
                            finalData = finalData.filter(
                                (fd) => fd.subID != d.subID
                            );
                            finalData.push(d);
                            if (!d.valid) {
                                allsubmissionchecks =
                                    allsubmissionchecks.filter(
                                        (checkbox) =>
                                            checkbox.id != `select${d.subID}`
                                    );
                                hide(getElement(`subslab${d.subID}`));
                            }
                        });
                        window.localStorage.setItem(
                            localStorageKey,
                            JSON.stringify(finalData)
                        );
                        message(`{% trans "Filtered" %}`);
                    },
                    () => bulkDialog.close()
                )
                .set("labels", {
                    ok: '{% trans "Yes" %}, {% trans "confirm" %}',
                    cancel: '{% trans "No" %}, {% trans "wait" %}!',
                });
        };

        getElements("rejectsubmission").forEach((reject) => {
            reject.onclick = (_) => {
                const rejectDialog = alertify
                    .confirm(
                        `{% trans "Confirm rejection" %}?`,
                        `<h4>Confirm to <span class="negative-text">reject</span> the following submission?</h4>
                    <button class="small primary" onclick="miniWindow('${reject.getAttribute(
                        "data-subItem"
                    )}')">${Icon("open_in_new")}View submission</button>
                `,
                        () => {
                            message(`rejecting...`);
                            finalData = finalData.filter(
                                (fd) =>
                                    fd.subID !=
                                    reject.getAttribute("data-subID")
                            );
                            finalData.push({
                                subID: reject.getAttribute("data-subID"),
                                valid: false,
                            });
                            allsubmissionchecks = allsubmissionchecks.filter(
                                (checkbox) =>
                                    checkbox.id !=
                                    `select${reject.getAttribute("data-subID")}`
                            );
                            window.localStorage.setItem(
                                localStorageKey,
                                JSON.stringify(finalData)
                            );
                            hide(
                                getElement(
                                    `subslab${reject.getAttribute(
                                        "data-subID"
                                    )}`
                                )
                            );
                        },
                        () => rejectDialog.close()
                    )
                    .set("labels", {
                        ok: '{% trans "Yes" %}, {% trans "reject this one" %}',
                        cancel: '{% trans "No" %}, {% trans "wait" %}!',
                    });
            };
        });

        getElement("finalsend").onclick = (_) => {
            if (!finalData.length) {
                if (
                    allsubmissionchecks.every((checkbox) => !checkbox.checked)
                ) {
                    finalData = allsubmissionchecks.map((checkbox) => ({
                        subID: String(
                            checkbox.getAttribute("data-subID")
                        ).trim(),
                        valid: true,
                    }));
                } else {
                    finalData = allsubmissionchecks.map((checkbox) => ({
                        subID: String(
                            checkbox.getAttribute("data-subID")
                        ).trim(),
                        valid: checkbox.checked,
                    }));
                }
            }
            alertify
                .confirm(
                    `{% trans "Send to judges" %}?`,
                    `<h4>Are you sure you want to send 
                <span class="positive-text">${
                    finalData.filter((fd) => fd.valid).length
                } submissions approved</span> by you
                to judges for final evaluation?
                This will also invalidate <span class="negative-text">${
                    finalData.filter((fd) => !fd.valid).length
                } submissions rejected</span>
                by you. This action is <span class="negative-text">{% trans "irreversible" %}</span>.
            </h4>`,
                    async () => {
                        message("Submitting...");
                        loader(true);
                        subLoader(true);
                        const data = await postRequest(
                            "{{moderation.approveCompeteLink}}",
                            {
                                submissions: finalData,
                            }
                        );
                        if (data.code === code.OK) {
                            success(
                                '{% trans "Filtered submissions submitted for judgement" %}'
                            );
                            window.location.reload();
                        } else {
                            loader(false);
                            subLoader(false);
                            error(data.error);
                        }
                    },
                    () => {}
                )
                .set("labels", { ok: "Yes, do it", cancel: "No, wait!" });
        };

        getElement("discardall").onclick = (_) => {
            alertify
                .confirm(
                    `Discard changes?`,
                    `<h4>{% trans "Are you sure to discard all changes you made?" %} {% trans "All rejected submissions will be restored, and you'll have to start again." %}</h4>`,
                    () => {
                        subLoader();
                        window.localStorage.removeItem(localStorageKey);
                        window.location.reload();
                    },
                    () => {}
                )
                .set("labels", { ok: "Yes, discard", cancel: "No, wait!" });
        };

        const allSubmissionsData = [];
        {% for sub in moderation.competition.getValidSubmissions %}
        allSubmissionsData.push({
            subID: "{{sub.getID}}",
            members: [
                {% for member in sub.getMembers %}
                {
                    id: "{{member.getUserID}}",
                    name: "{{member.getName}}",
                    email: "{{member.getEmail}}",
                    link: "{{member.getLink}}",
                    dp: "{{member.getDP}}",
                },
                {% endfor %}
            ],
        });
        {% endfor %}

        getElements("members-count-view").forEach((count) => {
            count.onclick = (_) => {
                const submission = allSubmissionsData.find(
                    (subm) => subm.subID == count.getAttribute("data-subID")
                );
                let mdata = "";
                submission.members.forEach((member) => {
                    mdata += `
                    <div class="pallete-slab">
                        <a onclick="miniWindow('${member.link}')"><img src="${member.dp}" class="w3-circle" width="30" /></a>
                        <strong>${member.name}</strong><br/>
                        <span>${member.email}</span>
                    </div>
                    `;
                });
                alertify.alert(
                    `<h6>{% trans "Members View" %} ({% trans "Only to verify authenticity" %})</h6>`,
                    mdata,
                    () => {}
                );
            };
        });
    }
}
