const compID = "{{compete.get_id}}";
const canEdit = "{{compete.canBeEdited}}" == "True";
const canDraft = "{{compete.canBeSetToDraft}}" == "True";
const canDelete = "{{compete.canBeDeleted}}" == "True";
const isUpcoming = "{{compete.isUpcoming}}" == "True";
const isHistory = "{{compete.isHistory}}" == "True";
const isActive = "{{compete.isActive}}" == "True";

const taskIDEs = getElements("task-view-segment").map(
    (e) =>
        new SimpleMDE({
            element: e,
            toolbar: false,
            status: false,
        })
);
taskIDEs.forEach((e) => e.togglePreview());

{% if compete.canBeSetToDraft %}
getElement("comp-make-draft").onclick = async () => {
    Swal.fire({
        title: "Convert to Draft?",
        text: "This will convert the competition to draft mode only if the competition is not yet live or there are no submissions.",
        denyButtonText: "Convert to Draft",
        showCancelButton: true,
        showDenyButton: true,
        showConfirmButton: false,
        cancelButtonText: "No, go back!",
    }).then(async (res) => {
        if (res.isDenied) {
            const data = await postRequest2({
                path: setUrlParams(URLS.DRAFT_DEL_COMP, compID),
                data: {
                    draft: true,
                    confirmed: res.isDenied,
                },
            });
            if (data && data.code == CODE.OK) {
                return refresh({});
            }
            error(data.error);
        }
    });
};
{% elif compete.is_draft %}
getElement("comp-publish-draft").onclick = async () => {
    Swal.fire({
        title: "Publish Competition?",
        text: "This will publish the competition to Knotters, and it will be then visible to everyone.",
        confirmButtonText: "Publish Competition",
        showCancelButton: true,
        showDenyButton: false,
        showConfirmButton: true,
        cancelButtonText: "No, go back!",
    }).then(async (res) => {
        if (res.isConfirmed) {
            const data = await postRequest2({
                path: setUrlParams(URLS.DRAFT_DEL_COMP, compID),
                data: {
                    draft: false,
                    confirmed: res.isConfirmed,
                },
            });
            if (data && data.code == CODE.OK) {
                return refresh({});
            }
            error(data.error);
        }
    });
};
{% endif %}

{% if compete.canBeDeleted %}
getElement("comp-delete-permanent").onclick = async () => {
    Swal.fire({
        title: "Delete permanently?",
        text: "This will DELETE the competition, only if the competition is not yet live or there are no submissions.",
        denyButtonText: "DELETE NOW",
        showDenyButton: true,
        showCancelButton: true,
        showConfirmButton: false,
        cancelButtonText: "No, go back!",
    }).then(async (res) => {
        if (res.isDenied) {
            const data = await postRequest2({
                path: setUrlParams(URLS.DRAFT_DEL_COMP, compID),
                data: {
                    delete: true,
                    confirmed: res.isDenied,
                },
            });
            if (data && data.code == CODE.OK) {
                futureMessage("The competition was deleted");
                return refer({ path: URLS.COMPETITIONS });
            }
            error(data.error);
        }
    });
};
{% endif %}

{% if compete.canBeEdited %}
getElement("compbannerfile").onchange = (e) => {
    handleCropImageUpload(
        e,
        "compbanner",
        "competebanneroutput",
        (_) => {
            getElement("competebannerimagebutton").innerHTML =
                "Selected banner";
        },
        8 / 2
    );
};
{% if compete.associate %}
getElement("compassociatefile").onchange = (e) => {
    handleCropImageUpload(
        e,
        "compassociate",
        "competeassociateoutput",
        (_) => {
            getElement("competeassociateimagebutton").innerHTML =
                "Selected associate";
            getElement("useAssociate").checked = true;
        },
        3.29166667
    );
};
{% endif %}

getElement("compendAt").addEventListener("blur", (e) => {
    if (e.target.value <= getElement("compstartAt").value) {
        error("Ending time should be greater than begin time!");
    }
    if (
        new Date(getElement("compstartAt").value).getTime() <=
        new Date().getTime()
    ) {
        error("Begin time should be greater than current time!");
    }
});
getElement("compstartAt").addEventListener("blur", (e) => {
    if (new Date(e.target.value).getTime() <= new Date().getTime()) {
        error("Begin time should be greater than current time!");
    }
    if (e.target.value >= getElement("compendAt").value) {
        error("Ending time should be greater than begin time!");
    }
});

{% endif %}
let excludemods = [
    {% for judge in compete.getJudges %}
    "{{judge.get_userid}}",
    {% endfor %}
];
let excludejudges = ["{{compete.getModerator.get_userid}}"];
let compjudgeIDs = [
    {% for judge in compete.getJudges %}
    "{{judge.get_userid}}",
    {% endfor %}
];
let comptopicIDs = [
    {% for topic in compete.getTopics %}
    "{{topic.get_id}}",
    {% endfor %}
];
let compmodID = "{{compete.getModerator.get_userid}}";

const loadSelectedJMTs = () => {
    {% if compete.canChangeJudges %}
    getElements("selected-compete-judge").forEach((btn) => {
        btn.onclick = (e) => {
            const id = btn.getAttribute("data-judgeID");
            if (compjudgeIDs.includes(id)) {
                excludemods = excludemods.filter((mid) => mid !== id);
                compjudgeIDs = compjudgeIDs.filter((id) => id !== id);
                btn.remove();
            }
        };
    });
    {% endif %}
    {% if compete.canChangeModerator %}
    getElements("selected-compete-mod").forEach((btn) => {
        btn.onclick = (e) => {
            compmodID = "";
            excludejudges = excludejudges.filter(
                (id) => id != btn.getAttribute("data-modID")
            );
            btn.hidden = true;
            btn.remove();
            show(getElement("selectmodbutton"));
        };
    });
    {% endif %}
    {% if compete.canBeEdited %}
    getElements("selected-compete-topic").forEach((btn) => {
        btn.onclick = (e) => {
            const id = btn.getAttribute("data-topicID");
            if (comptopicIDs.includes(id)) {
                comptopicIDs = comptopicIDs.filter((id) => id !== id);
                btn.remove();
            }
        };
    });
    {% endif %}
};
loadSelectedJMTs();
{% if compete.canBeEdited %}
getElement("addtopicbutton").onclick = (_) => {
    Swal.fire({
        title: "Search topics",
        html: `
            <input id='topicquery' placeholder="Type to search topic" class="wide"></input><br/><br/>
            <div id='topicqueryresult'>
            </div>
            <div><a onclick="newTab(setUrlQueries(URLS.LABELS,{tab:1}))">Click here</a> to see available topics.</div>
            `,
        didOpen: () => {
            getElement("topicquery").focus();
            getElement("topicquery").oninput = async (e) => {
                const data = await postRequest(URLS.TOPICSEARCH, {
                    query: e.target.value,
                });
                if (!data) return;
                if (data.code === code.OK && data.topic) {
                    getElement(
                        "topicqueryresult"
                    ).innerHTML = `<button class="primary" type='button' id="${data.topic.id}">${data.topic.name}</button>`;
                    getElement(data.topic.id).onclick = (e) => {
                        const id = e.target.id.replaceAll("-", "");
                        if (comptopicIDs.includes(id)) {
                            return error("Already selected");
                        }
                        comptopicIDs.push(id);
                        getElement(
                            "selectedtopicsview"
                        ).innerHTML += `<button type='button' class="primary negative-text selected-compete-topic" data-topicID='${id}' id="removetopic${id}">${Icon(
                            "close"
                        )}${data.topic.name}</button>`;
                    };
                } else {
                    getElement("topicqueryresult").innerHTML = "No results.";
                }
            };
        },
    }).then(() => {
        loadSelectedJMTs();
    });
};
{% endif %}
{% if compete.canChangeJudges %}
getElement("addjudgebutton").onclick = (_) => {
    Swal.fire({
        title: "Search your judge",
        html: `
            <input id='judgequery' placeholder="Type to search your judge" class="wide"></input><br/><br/>
            <div id='judgequeryresult'>
            </div><br/>
            <div>Judge(s) to mark submissions with points according to topics, after competition ends. 
                Make sure they know about your competition beforehand. Only mentors can be judges.
                You'll be responsible for the actions of judge(s) you choose in this competition.
                You can manage your mentors <a href="${URLS.MODERATORS}" target="_blank">from here</a>.
            </div>
            `,
        didOpen: () => {
            getElement("judgequery").oninput = async (e) => {
                const data = await postRequest(URLS.JUDGESEARCH, {
                    query: e.target.value,
                    excludeIDs: excludejudges,
                });
                if (!data) return;
                if (data.code === code.OK && data.judge) {
                    getElement("judgequeryresult").innerHTML = `
                        <button class="primary" type='button' id="${
                            data.judge.id
                        }">
                            <img src="${
                                data.judge.dp
                            }" width="20" class="w3-circle primary" /> ${
                        data.judge.name
                    }</button>
                            <a onclick="miniWindow('${data.judge.url}')">${Icon(
                        "open_in_new"
                    )}</a>`;
                    getElement(data.judge.id).onclick = (e) => {
                        const id = e.target.id.replaceAll("-", "");
                        if (compjudgeIDs.includes(id)) {
                            return error("Already selected");
                        }
                        excludemods.push(id);
                        compjudgeIDs.push(id);
                        getElement("selectedjudgesview").innerHTML += `
                            <button type='button' title="Judge" class="primary negative-text selected-compete-judge" data-judgeID='${id}' id="removejudge${id}">
                            ${Icon("close")}<img src="${
                            data.judge.dp
                        }" width="20" class="w3-circle primary" /> ${
                            data.judge.name
                        }</button>`;
                    };
                } else {
                    getElement("judgequeryresult").innerHTML = "No results.";
                }
            };
        },
    }).then(() => {
        loadSelectedJMTs();
    });
};
{% endif %}
{% if compete.canChangeModerator %}
getElement("selectmodbutton").onclick = (ebtn) => {
    Swal.fire({
        title: "Search your moderator",
        html: `
            <input id='modquery' placeholder="Type to search your moderator" class="wide"></input><br/><br/>
            <div id='modqueryresult'>
            </div><br/>
            <div>A moderator to moderate submissions before judgement, after competition ends. Make sure they know about your competition beforehand.
                You'll be responsible for the actions of moderator you choose in this competition.
                You can manage your moderators <a href="${URLS.MODERATORS}" target="_blank">from here</a>.
            </div>
            `,
        didOpen: () => {
            let lastmodid = "";
            getElement("modquery").oninput = async (e) => {
                const data = await postRequest2({
                    path: URLS.MODSEARCH,
                    data: {
                        query: e.target.value,
                        excludeIDs: excludemods,
                    },
                });
                if (!data) return;
                if (data.code === code.OK && data.mod) {
                    getElement("modqueryresult").innerHTML = `
                        <button class="primary" type='button' id="${
                            data.mod.id
                        }">
                            <img src="${
                                data.mod.dp
                            }" width="20" class="w3-circle" /> ${data.mod.name}
                        </button><a onclick="miniWindow('${
                            data.mod.url
                        }')">${Icon("open_in_new")}</a>
                        `;
                    getElement(data.mod.id).onclick = (e) => {
                        const id = e.target.id.replaceAll("-", "");
                        compmodID = id;
                        excludejudges = excludejudges.filter(
                            (id) => id != lastmodid
                        );
                        excludejudges.push(id);
                        lastmodid = id;
                        getElement("selectedmodview").innerHTML = `
                            <button type='button' title="Moderator" class="primary negative-text selected-compete-mod" data-modID='${id}' id="removemod${id}">
                                ${Icon("close")}<img src="${
                            data.mod.dp
                        }" width="20" class="w3-circle primary" /> ${
                            data.mod.name
                        }
                            </button>`;
                        hide(getElement("selectmodbutton"));
                        success("Moderator selected!");
                    };
                } else {
                    getElement("modqueryresult").innerHTML = "No results.";
                }
            };
        },
    }).then(() => {
        loadSelectedJMTs();
    });
};
{% endif %}
{% if compete.canBeEdited%}
getElement("edit-details-action").addEventListener("click", () => {
    taskIDEs.forEach((e) => {
        e.togglePreview();
        e.createToolbar();
    });
});
{% endif %}
{% if compete.canBeEdited or compete.canChangeJudges or compete.canChangeModerator or not compete.resultDeclared %}
getElement("discard-edit-compete-info").addEventListener("click", () => {
    {% if compete.canBeEdited %}
    taskIDEs.forEach((e) => e.togglePreview());
    {% endif %}
    refresh({});
});
getElement("save-edit-compete-info").addEventListener("click", async () => {
    {% if compete.canBeEdited %}
    taskIDEs.forEach((e) => e.toTextArea());
    {% endif %}
    const data = await postRequest2({
        path: setUrlParams(URLS.EDIT_COMP, compID),
        data: {
            {% if compete.canBeEdited %}
            comptitle: getElement("comptitle").value,
            comptagline: getElement("comptagline").value,
            compshortdesc: getElement("compshortdesc").value,
            compbanner: getElement("compbanner").value,
            {% if compete.associate %}
            compassociate: getElement("compassociate").value,
            {% endif %}
            compdesc: getElement("compdesc").value,
            compstartAt: getElement("compstartAt").value,
            compendAt: getElement("compendAt").value,
            compeachTopicMaxPoint: Number(
                getElement("compeachTopicMaxPoint").value
            ),
            {% if compete.reg_fee %}
            compregfee: getElement("compregfee").value,
            compfeelink: getElement("compfeelink").value,
            {% endif %}
            {% endif %}
            {% if compete.canChangeModerator %}
            compmodID,
            {% endif %}
            comptopicIDs,
            {% if compete.canChangeJudges %}
            compjudgeIDs,
            {% endif %}
            {% if compete.canBeEdited %}
            comptaskSummary: getElement("comptaskSummary").value,
            comptaskDetail: getElement("comptaskDetail").value,
            comptaskSample: getElement("comptaskSample").value,
            {% endif %}
        },
    });
    if (data && data.code == CODE.OK) {
        futureMessage("Competition details updated successfully");
        return refresh({});
    } else error(data.error);
});
{% endif %}
