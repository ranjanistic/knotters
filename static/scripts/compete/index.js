const loadTabScript = (tab) => {};

initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(setUrlParams(URLS.INDEXTAB, tab.id)),
    uniqueID: "competitionstab",
    tabsClass: "compete-nav-tab",
    onShowTab: loadTabScript,
    activeTabClass: "active",
    inactiveTabClass: "primary text-primary",
});
