getElement("addperksbutton").onclick = (_) => {
    const parent = document.getElementById("perkDetails");
    const position = parent.childElementCount + 1;
    const newChild = document.createElement("div");
    newChild.classList.add(
        "w3-col",
        "w3-third",
        "w3-padding-small",
        "w3-center"
    );
    newChild.innerHTML = `                
        <div class="pallete accent">
            
            <i class="w3-jumbo material-icons">emoji_events</i>
            <h1>${numsuffix(position)}</h1>
            <h6 class="pallete">
                <input class="wide create-compete-input" required placeholder="Perk for Rank ${position}" type="text" name="compperk${position}" id="compperk${position}">
            </h6>
        </div>
    `;
    parent.insertBefore(newChild, parent.childNodes[position + 3]);
};

initializeTabsView({
    onEachTab: async (tab) => {
        getElements("side-nav-tab-view").forEach((v) => {
            visible(v, v.id.startsWith(tab.id));
        });
    },
    uniqueID: "competetab",
    tabsClass: "side-nav-tab",
    activeTabClass: "active",
    setDefaultViews: false,
    onShowTab: (tab) => {},
});

let excludemods = [];
let excludejudges = [];
getElements("create-compete-input").forEach((element) => {
    if (!Array.from(element.classList).includes("no-retain")) {
        element.value = sessionStorage.getItem(
            `create-compete-input-${element.id}`
        );
        element.oninput = (e) => {
            sessionStorage.setItem(
                `create-compete-input-${element.id}`,
                element.value
            );
        };
    }
});
getElement("useAssociate").onchange = (e) => {
    if (!e.target.checked) {
        getElement("compassociate").value = "";
    } else {
        if (getElement("competeassociateoutput").src.endsWith("default.png")) {
            e.target.checked = false;
            return error("Select the association image");
        }
        getElement("compassociate").value = getElement(
            "competeassociateoutput"
        ).src;
    }
};
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
                        let existing = String(
                            getElement("topicIDs").value
                        ).trim();
                        if (existing.includes(id)) {
                            return error("Already selected");
                        }
                        getElement("topicIDs").value = existing + "," + id;
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
        getElements("selected-compete-topic").forEach((btn) => {
            btn.onclick = (e) => {
                const id = btn.getAttribute("data-topicID");
                if (getElement("topicIDs").value.includes(id)) {
                    getElement("topicIDs").value = getElement(
                        "topicIDs"
                    ).value.replaceAll(`,${id}`, "");
                    btn.remove();
                }
            };
        });
    });
};
getElement("addjudgebutton").onclick = (_) => {
    Swal.fire({
        title: "Search your judge",
        html: `
        <input id='judgequery' placeholder="Type to search your judge" class="wide"></input><br/><br/>
        <div id='judgequeryresult'>
        </div><br/>
        <div>Judge(s) to mark submissions with points according to topics, after competition ends. Make sure they know about your competition beforehand.
            You'll be responsible for the actions of judge(s) you choose in this competition.
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
                    <button class="primary" type='button' id="${data.judge.id}">
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
                        let existing = String(
                            getElement("judgeIDs").value
                        ).trim();
                        if (existing.includes(id)) {
                            return error("Already selected");
                        }
                        excludemods.push(id);
                        getElement("judgeIDs").value = existing + "," + id;
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
        getElements("selected-compete-judge").forEach((btn) => {
            btn.onclick = (e) => {
                const id = btn.getAttribute("data-judgeID");
                if (getElement("judgeIDs").value.includes(id)) {
                    excludemods = excludemods.filter((mid) => mid !== id);
                    getElement("judgeIDs").value = getElement(
                        "judgeIDs"
                    ).value.replaceAll(`,${id}`, "");
                    btn.hidden = true;
                    btn.remove();
                }
            };
        });
    });
};
getElement("selectmodbutton").onclick = (ebtn) => {
    Swal.fire({
        title: "Search your moderator",
        html: `
        <input id='modquery' placeholder="Type to search your moderator" class="wide"></input><br/><br/>
        <div id='modqueryresult'>
        </div><br/>
        <div>A moderator to moderate submissions before judgement, after competition ends. Make sure they know about your competition beforehand.
            You'll be responsible for the actions of moderator you choose in this competition.
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
                    <button class="primary" type='button' id="${data.mod.id}">
                        <img src="${
                            data.mod.dp
                        }" width="20" class="w3-circle" /> ${data.mod.name}
                    </button><a onclick="miniWindow('${data.mod.url}')">${Icon(
                        "open_in_new"
                    )}</a>
                    `;
                    getElement(data.mod.id).onclick = (e) => {
                        const id = e.target.id.replaceAll("-", "");
                        getElement("compmodID").value = id;
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
        getElements("selected-compete-mod").forEach((btn) => {
            btn.onclick = (e) => {
                getElement("compmodID").value = "";
                excludejudges = excludejudges.filter(
                    (id) => id != btn.getAttribute("data-modID")
                );
                btn.hidden = true;
                btn.remove();
                show(getElement("selectmodbutton"));
            };
        });
    });
};
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

getElement("search-qualifier-comp-action").onclick = async () => {
    let query = getElement("search-qualifier-comp-input").value.trim();
    if (!query) return message("Type something to search");
    const viewer = getElement("qualifier-comp-search-result");
    const data = await postRequest2({
        path: setUrlParams(URLS.Compete.BROWSE_SEARCH),
        data: { query, limit: 1 },
    });
    if (!data) return;
    if (data.code != code.OK) return error(data.error);
    if (!data.competitions.length)
        return (viewer.innerHTML = "<br/>No competitions found");
    const comp = data.competitions[0];
    viewer.innerHTML = `
        <br/>
        <div class="pallete-slab pointer" id='search-competition-result'>
            <img class="pallete-slab no-pad primary" src="${comp.banner}" width="100" /><br/>
            <strong>${comp.title}</strong><br/>
            ${comp.tagline}
            <br/>
            <a href="${comp.url}" target="_blank"><button type="button" class="small primary">View</button></a>
            <button class="positive small" type="button" id="qualifier-comp-result-select">Select</button>
        </div><br/>
    `;
    getElement("qualifier-comp-result-select").onclick = (_) => {
        const selectedviewer = getElement("qualifier-comp-preview");
        selectedviewer.innerHTML = `
        <br/>
            <div class="pallete-slab" id='search-competition-result'>
                <img class="pallete-slab no-pad primary" src="${comp.banner}" width="100" /><br/>
                <strong>${comp.title}</strong><br/>
                ${comp.tagline}
                <br/>
                <a href="${comp.url}" target="_blank"><button type="button" class="small primary">View</button></a>
                <button type="button" class="negative small" id="selected-qualifier-comp-remove">Remove</button>
            </div><br/>
        `;
        selectedviewer.innerHTML += `<br/>
        <strong>Provide the maximum rank required in linked competition to qualify for your competition</strong><br/>
        <input type='number' name='qualifier-competition-rank' class="create-compete-input" title='Qualifing rank' required inputmode='numeric' placeholder='Qualifing rank' />`;
        getElement("qualifier-competition-id").value = comp.id;
        getElement("selected-qualifier-comp-remove").onclick = (_) => {
            getElement("qualifier-competition-id").value = "";
            selectedviewer.innerHTML = "";
            showElement("select-qualifier-competition-init");
        };
        hideElement("select-qualifier-competition-init");
        getElement("save-edit-qualifier-comp").click();
    };
};
const editorsParams = [
    {
        element: getElement("comptaskSummary"),
        autosave: {
            enabled: true,
            uniqueId: "comptaskSummary",
            delay: 1000,
        },
    },
    {
        element: getElement("comptaskDetail"),
        autosave: {
            enabled: true,
            uniqueId: "comptaskDetail",
            delay: 1000,
        },
    },
    {
        element: getElement("comptaskSample"),
        autosave: {
            enabled: true,
            uniqueId: "comptaskSample",
            delay: 1000,
        },
    },
];
let tasksEditors = editorsParams.map((editor) => new SimpleMDE(editor));
getElement("create-compete-form-submit-button").onclick = (e) => {
    e.preventDefault();
    tasksEditors.forEach((editor) => editor.toTextArea());
    if (
        !getElements("create-compete-input").every((element) => {
            if (!element.value && element.required) {
                error(
                    `${
                        element.title || element.placeholder || "Some fields"
                    } not filled.`
                );
                tasksEditors = editorsParams.map(
                    (editor) => new SimpleMDE(editor)
                );
                element.scrollIntoView();
                element.focus();
                return false;
            }
            return true;
        })
    )
        return;
    subLoader();
    getElement("create-compete-form").submit();
};
