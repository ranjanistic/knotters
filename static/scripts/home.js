if(getElements("domain-colab-tab").length){
    initializeTabsView({
        tabsClass: "domain-colab-tab",
        viewID: "domain-colab-tab-view",
        activeTabClass: "primary pallete",
        inactiveTabClass: "accent pallete-slab",
        onEachTab: async (tab) => {
            return await getRequest2({
                path: setPathParams(URLS.HOME_DOMAINS, tab.id),
                silent: true,
                allowCache: true
            });
        },
        autoShift: true,
        autoShiftDuration: 5000,
        setDefaultViews: false,
    });
}

restartIntros()