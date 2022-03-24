const loadTabScript = (tab) => {
    getElements("switch-compete-home-tab").forEach((action) => {
        action.onclick = () => {
            getElement(action.getAttribute("data-target")).click();
        };
    });
};

initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(setUrlParams(URLS.INDEXTAB, tab.id)),
    uniqueID: "competitionstab",
    tabsClass: "compete-nav-tab",
    onShowTab: loadTabScript,
    activeTabClass: "active",
    inactiveTabClass: "primary text-primary",
});
