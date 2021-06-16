
intializeTabsView(
    async (tabID) => {
        return await getRequest(`/competitions/competeTab/${compID}/${tabID}`);
    },
    "competetab",
    "side-nav-tab",
    "active"
);
