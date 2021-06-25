initializeTabsView(
    async (tabID) => {
        return await getRequest(`${ROOT}/indexTab/${tabID}`);
    },
    "competitionstab",
    "compete-nav-tab",
);


var values = ["hello", "bye"];

handleDropDowns(
    "dropdown-box",
    "compete-dropdown",
    values
)