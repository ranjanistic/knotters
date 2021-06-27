
initializeTabsView({
    onEachTab: async (tabID) => {
        return await getRequest(`/competitions/competeTab/${compID}/${tabID}`);
    },
    uniqueID:"competetab",
    tabsClass:"side-nav-tab",
    activeTabClass:"active"
});
