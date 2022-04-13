const loadTabScript = (tab) => {
    getElements("switch-compete-home-tab").forEach((action) => {
        action.onclick = () => {
            getElement(action.getAttribute("data-target")).click();
        };
    });
    getElements("browse-admire-compete-action").forEach((act) => {
        act.onclick = async (_) => {
            if(!AUTHENTICATED){
                return refer({
                    path: URLS.Auth.LOGIN,
                    query: {
                        next: window.location.pathname,
                    }
                });
            }
            const cid = act.getAttribute("data-compID");
            const admire = act.getAttribute("data-admires") == "0";
            const data = await postRequest2({
                path: setUrlParams(
                    URLS.Compete.TOGGLE_ADMIRATION,
                    cid
                ),
                data: {
                    admire,
                },
                retainCache: true,
            });
            if (data.code !== code.OK) {
                return error(data.error);
            }
            act.setAttribute("data-admires", admire ? 1 : 0);
            act.classList[admire ? "add" : "remove"]("positive");
            act.classList[admire ? "remove" : "add"]("primary");
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
