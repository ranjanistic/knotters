const loadDemoteMnts = () => {
    getElements("demote-mentor").forEach((demote) => {
        demote.onclick = (e) => {
            alertify
                .confirm(
                    "Demote as mentor?",
                    `<h5>Are you sure that you want to ${NegativeText(
                        "demote"
                    )} 
                <a href="${e.target.getAttribute(
                    "data-profileurl"
                )}" target="_blank">${e.target.getAttribute("data-name")}</a>
                 as a mentor on ${APPNAME}? Their pending mentorships will be transferred to a new mentor. (You are not deleting their account)</h5>`,
                    () => {},
                    async () => {
                        const mntID = e.target.getAttribute("data-userID");
                        const mntname = e.target.getAttribute("data-name");
                        const data = await postRequest2({
                            path: URLS.REMOVE_MENTOR,
                            data: { mntID },
                        });
                        if (!data) return;
                        if (data.code == code.OK) {
                            message(`Demoted ${mntname} as mentor`);
                            return hideElement(`pallete-demote-${mntID}`);
                        }
                        error(data.error);
                    }
                )
                .set("labels", { cancel: "Yes, demote", ok: "No, wait" })
                .set("closable", false);
        };
    });
};

getElement("search-mnt-input").oninput = async (e) => {
    const resview = getElement("mnt-search-results");
    if (!e.target.value.trim()) {
        resview.innerHTML = "";
        return;
        //         loadAddMnts()
    }
    const data = await postRequest2({
        path: URLS.MNTSEARCH,
        data: { query: e.target.value },
    });
    if (!data) return;
    if (data.code !== code.OK || !data.mnt) return;
    const mnt = data.mnt;
    setHtmlContent(
        resview,
        `<div class="w3-row pallete-slab" id="pallete-demote-${data.mnt.userID}">
                <div class="w3-col s2 m1">
                    <a href="${mnt.url}" target="_blank"><img src="${mnt.dp}" class="w3-circle primary" width="50" /></a>
                </div>
                <div class="w3-col s10 m8 w3-padding-small">
                    <div class="w3-row">
                        ${mnt.name}
                    </div>
                    <div class="w3-row">
                        ${mnt.email}
                    </div>
                </div>
            </div>`
    );
};

getElement("search-profile-input").oninput = async (e) => {
    const resview = getElement("profile-search-results");
    if (!e.target.value.trim()) {
        resview.innerHTML = "";
        return loadAddMnts();
    }
    const data = await postRequest2({
        path: URLS.ELGIBLE_MNTSEARCH,
        data: { query: e.target.value },
    });
    if (!data) return;
    if (data.code !== code.OK || !data.mnt) return;
    const mnt = data.mnt;
    setHtmlContent(
        resview,
        `<div class="w3-row pallete-slab" id="pallete-promote-${data.mnt.userID}">
                <div class="w3-col s2 m1">
                    <a href="${mnt.url}" target="_blank"><img src="${mnt.dp}" class="w3-circle primary" width="50" /></a>
                </div>
                <div class="w3-col s10 m8 w3-padding-small">
                    <div class="w3-row">
                        ${mnt.name}
                    </div>
                    <div class="w3-row">
                        ${mnt.email}
                    </div>
                </div>
                <div class="w3-col s4 m3 w3-padding-small">
                    <div class="w3-row w3-right">
                        <button class="small positive promote-mentor" data-profileurl="${mnt.url}" data-name="${mnt.name}" data-userID="${mnt.userID}">Promote</button>
                    </div>
                </div>
            </div>`,
        loadAddMnts
    );
};

const loadAddMnts = () => {
    getElements("promote-mentor").forEach((promote) => {
        promote.onclick = (e) => {
            alertify
                .confirm(
                    "Promote as mentor?",
                    `<h5>Are you sure that you want to promote 
                    <a href="${e.target.getAttribute(
                        "data-profileurl"
                    )}" target="_blank">${e.target.getAttribute("data-name")}</a>
                    as a mentor on ${APPNAME}?</h5>`,
                    async () => {
                        const userID = e.target.getAttribute("data-userID");
                        const username = e.target.getAttribute("data-name");
                        const data = await postRequest2({
                            path: URLS.ADD_MENTOR,
                            data: { userID },
                        });
                        if (!data) return;
                        if (data.code == code.OK) {
                            message(`Promoted ${username} as mentor`);
                            hideElement(`pallete-promote-${userID}`);
                            let newmnt = getElement(`pallete-promote-${userID}`)
                                .innerHTML.replaceAll("promote-", "demote-")
                                .replaceAll("positive", "negative")
                                .replaceAll("Promote", "Demote");
                            getElement(
                                "new-mentors-view"
                            ).innerHTML += `<div class="w3-row pallete-slab" id="pallete-demote-${userID}">${newmnt}</div>`;
                            loadDemoteMnts();
                            return;
                        }
                        error(data.error);
                    },
                    () => {}
                )
                .set("labels", { ok: "Yes, promote", cancel: "No, wait" })
                .set("closable", false);
        };
    });
};
loadDemoteMnts();
loadAddMnts();
