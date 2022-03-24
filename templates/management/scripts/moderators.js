const loadDemoteMods = () => {
    getElements("demote-moderator").forEach((demote) => {
        demote.onclick = (e) => {
            Swal.fire({
                title: "Demote moderator",
                html: `<h5>Are you sure that you want to ${NegativeText(
                    "demote"
                )} 
                <span class="positive-text pointer" onclick="miniWindow('${demote.getAttribute(
                    "data-profileurl"
                )}')">${demote.getAttribute("data-name")}</span>
                 as a moderator on ${APPNAME}? Their pending moderations will be transferred to a new moderator. (You are not deleting their account)</h5>`,
                imageUrl: demote.getAttribute("data-dp"),
                imageWidth: 100,
                showCancelButton: true,
                showConfirmButton: false,
                showDenyButton: true,
                denyButtonText: "Yes, demote!",
            }).then(async (result) => {
                if (result.isDenied) {
                    const modID = e.target.getAttribute("data-userID");
                    const modname = e.target.getAttribute("data-name");
                    const data = await postRequest2({
                        path: URLS.REMOVE_MODERATOR,
                        data: { modID },
                    });
                    if (!data) return;
                    if (data.code == code.OK) {
                        message(`Demoted ${modname} from moderator`);
                        return hideElement(`pallete-demote-${modID}`);
                    }
                    error(data.error);
                }
            });
        };
    });
};

getElement("search-mod-input").oninput = async (e) => {
    const resview = getElement("mod-search-results");
    if (!e.target.value.trim()) {
        resview.innerHTML = "";
        return;
        //         loadAddMods()
    }
    const data = await postRequest2({
        path: URLS.MODSEARCH,
        data: { query: e.target.value },
    });
    if (!data) return;
    if (data.code !== code.OK || !data.mod) return;
    const mod = data.mod;
    setHtmlContent(
        resview,
        `<div class="w3-row pallete-slab" id="pallete-demote-${data.mod.userID}">
                <div class="w3-col s2 m1">
                    <a onclick="miniWindow('${mod.url}')"><img src="${mod.dp}" class="w3-circle primary" width="50" /></a>
                </div>
                <div class="w3-col s10 m8 w3-padding-small">
                    <div class="w3-row">
                        ${mod.name}
                    </div>
                    <div class="w3-row">
                        ${mod.email}
                    </div>
                </div>
            </div>`
    );
};

getElement("search-profile-input").oninput = async (e) => {
    const resview = getElement("profile-search-results");
    if (!e.target.value.trim()) {
        resview.innerHTML = "";
        return loadAddMods();
    }
    const data = await postRequest2({
        path: URLS.ELGIBLE_MODSEARCH,
        data: { query: e.target.value },
    });
    if (!data) return;
    if (data.code !== code.OK || !data.mod) return;
    const mod = data.mod;
    setHtmlContent(
        resview,
        `<div class="w3-row pallete-slab" id="pallete-promote-${data.mod.userID}">
                <div class="w3-col s2 m1">
                    <a onclick="miniWindow('${mod.url}')"><img src="${mod.dp}" class="w3-circle primary" width="50" /></a>
                </div>
                <div class="w3-col s10 m8 w3-padding-small">
                    <div class="w3-row">
                        ${mod.name}
                    </div>
                    <div class="w3-row">
                        ${mod.email}
                    </div>
                </div>
                <div class="w3-col s4 m3 w3-padding-small">
                    <div class="w3-row w3-right">
                        <button class="small positive promote-moderator"  data-dp="${mod.dp}" data-profileurl="${mod.url}" data-name="${mod.name}" data-userID="${mod.userID}">Promote</button>
                    </div>
                </div>
            </div>`,
        loadAddMods
    );
};

const loadAddMods = () => {
    getElements("promote-moderator").forEach((promote) => {
        promote.onclick = (e) => {
            Swal.fire({
                title: "Promote as moderator?",
                html: `<h5>Are you sure that you want to ${PositiveText(
                    "promote"
                )} 
                        <span class="positive-text" onclick="miniWindow('${promote.getAttribute(
                            "data-profileurl"
                        )}')">${promote.getAttribute("data-name")}</span>
                        as a moderator on ${APPNAME}?</h5>`,
                imageUrl: promote.getAttribute("data-dp"),
                imageWidth: 100,
                showCancelButton: true,
                confirmButtonText: "Yes, promote",
                cancelButtonText: "No, wait",
            }).then(async (result) => {
                if (result.isConfirmed) {
                    const userID = e.target.getAttribute("data-userID");
                    const username = e.target.getAttribute("data-name");
                    const data = await postRequest2({
                        path: URLS.ADD_MODERATOR,
                        data: { userID },
                    });
                    if (!data) return;
                    if (data.code == code.OK) {
                        message(`Promoted ${username} as moderator`);
                        hideElement(`pallete-promote-${userID}`);
                        let newmod = getElement(`pallete-promote-${userID}`)
                            .innerHTML.replaceAll("promote-", "demote-")
                            .replaceAll("positive", "negative")
                            .replaceAll("Promote", "Demote");
                        getElement(
                            "new-moderators-view"
                        ).innerHTML += `<div class="w3-row pallete-slab" id="pallete-demote-${userID}">${newmod}</div>`;
                        loadDemoteMods();
                        return;
                    }
                    error(data.error);
                }
            });
        };
    });
};
loadDemoteMods();
loadAddMods();
