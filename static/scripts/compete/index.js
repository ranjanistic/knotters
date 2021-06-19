intializeTabsView(
    async (tabID) => {
        return await getRequest(`${ROOT}/indexTab/${tabID}`);
    },
    "competitionstab",
    "compete-nav-tab",
);
