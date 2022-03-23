initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest(setUrlParams(URLS.REPORT_FEED_TYPE, tab.id));
    },
    uniqueID: "reportfeedtab",
    onShowTab: (tab) => {}
})