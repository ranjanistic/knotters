const loadTabScript = (tab) => {

};
initializeTabsView({
    onEachTab: async (tab) => await getRequest(`${ROOT}/indexTab/${tab.id}`),
    uniqueID: "competitionstab",
    tabsClass: "compete-nav-tab",
    onShowTab: loadTabScript,
});
