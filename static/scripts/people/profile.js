const tabs = getElements("nav-tab"),
    tabview = getElement("tabview");

const showTabLoading = () => {
    tabview.innerHTML = `<div class="loader" id="loader"></div>`;
    openSpinner();
};
const showTabError = () => {
    tabview.innerHTML = "Error";
};

const showTabContent = (content) => {
    tabview.innerHTML = content;
};

tabs.forEach(async (tab, t) => {
    tab.onclick = async () => {
        showTabLoading();
        tabs.forEach((tab1, t1) => {
            if (t1 === t) {
                tab1.classList.add("positive");
                tab1.classList.remove("primary");
            } else {
                tab1.classList.remove("positive");
                tab1.classList.add("primary");
            }
        });
        const response = await getRequest(
            `/people/profiletab/${userID}/${tab.id}`
        );
        hideSpinner();
        return response ? showTabContent(response) : showTabError();
    };
});

tabs[0].click();

if (selfProfile) {
    loadGlobalEditors();
}

