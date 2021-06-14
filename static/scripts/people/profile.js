intializeTabsView(async (tabID) => {
    return await getRequest(`/people/profiletab/${userID}/${tabID}`);
}, "profiletab");

intializeTabsView(
    async (tabID) => {
        return await getRequest(`/people/settingtab/${tabID}`);
    },
    "profilestab",
    "set-tab",
    "active",
    "primary",
    "stabview",
    "sloader"
);

if (selfProfile) {
    loadGlobalEditors();
}
