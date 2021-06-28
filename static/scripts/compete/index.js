const loadTabScript = (tabID) => {

};
initializeTabsView({
    onEachTab: async (tabID) => await getRequest(`${ROOT}/indexTab/${tabID}`),
    uniqueID: "competitionstab",
    tabsClass: "compete-nav-tab",
    onShowTab: loadTabScript,
});
