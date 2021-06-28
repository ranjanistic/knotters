let compdata = {};

if (isActive) {
    (async () => {
        const data = await postRequest(`${ROOT}/data/${compID}`);
        if (data.code == "OK") {
            compdata = { ...data };
            let timeleft = data.timeleft;
            setInterval(() => {
                getElement("remainingTime").innerHTML = timeleft;
                timeleft -= 1;
            }, 1000);
        }
    })();
}

const loadTabScript = (tab) => {
    switch (tab.id) {
        case "submission": {
            if (isActive) {
                if (compdata.participated) {
                    getElements("remove-person").forEach((remove) => {
                        remove.onclick = (_) => {
                            alertify.alert(
                                `Remove teammate`,
                                `
                            <div class="w3-row">
                                <h4>Are you sure you want to <span class="negative-text">remove</span> 
                                ${remove.getAttribute("data-name")}?</h4>
                                <form method="POST" action="${ROOT}/remove/${compdata.subID}/${remove.getAttribute("data-userID")}">
                                    ${csrfHiddenInput(csrfmiddlewaretoken)}
                                    <button class="negative">Yes, remove</button>
                                </form>
                            </div>`,
                            ).set({'label':'Cancel'})
                        };
                    });
                }
            }
        }
    }
};

initializeTabsView({
    onEachTab: async (tab) =>
        await getRequest(`${ROOT}/competeTab/${compID}/${tab.id}`),
    uniqueID: "competetab",
    tabsClass: "side-nav-tab",
    activeTabClass: "active",
    onShowTab: loadTabScript,
});
