getElement("addSocialLinkButton").onclick = (_) => {
    const parent = getElement("social-links");
    if (parent.childElementCount === 5)
        return message("Maximun URLs limit reached");
    const linkNumber = parent.childElementCount + 1;
    const newChild = document.createElement("div");
    newChild.innerHTML = `
        <input class="create-project-input wide" type="url" placeholder="Link to any relevant site" name="sociallink${linkNumber}" id=${linkNumber} /><br/><br/>
    `;
    parent.insertBefore(newChild, parent.childNodes[0]);
};

initializeTabsView({
    uniqueID: "license",
    activeTabClass: "positive text-positive",
    inactiveTabClass: "primary dead-text",
    tabsClass: "license-choice",
    onEachTab: (tab) => {
        getElement("license").value = tab.id;
    },
    selected: 0,
});
getElements("create-project-input").forEach((element) => {
    if (!Array.from(element.classList).includes("no-retain")) {
        element.value = sessionStorage.getItem(
            `create-freeproject-input-${element.id}`
        );
        element.addEventListener("input", (e) => {
            sessionStorage.setItem(
                `create-freeproject-input-${element.id}`,
                element.value
            );
        });
    }
});
getElement("uploadprojectimage").onchange = (e) => {
    handleCropImageUpload(e, "projectimagedata", "projectimageoutput", (_) => {
        getElement("uploadprojectimagelabel").innerHTML = "Selected";
    });
};
getElement("projectnickname").oninput = async (e) => {
    let nickname = String(e.target.value).toLowerCase().trim();
    nickname = nickname.replace(/[^a-z0-9\-]/g, "-").split('-').filter((k)=>k.length).join('-');
    if (!nickname) return;
    e.target.value = nickname;
};

getElement("projectnickname").onchange = async (e) => {
    let nickname = String(e.target.value).toLowerCase().trim();
    nickname = nickname.replace(/[^a-z0-9\-]/g, "-").split('-').filter((k)=>k.length).join('-');
    if (!nickname) return;
    e.target.value = nickname;
    const data = await postRequest(
        setUrlParams(URLS.CREATEVALIDATEFIELD, "nickname"),
        { nickname }
    );
    if (!data) return;
    if (data.code !== code.OK) return error(data.error);
    return success(`'${nickname}' is available!`);
};
