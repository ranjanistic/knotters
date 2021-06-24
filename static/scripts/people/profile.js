initializeTabsView(async (tabID) => {
    return await getRequest(`/people/profiletab/${userID}/${tabID}`);
}, "profiletab");

if (selfProfile) {
    initializeTabsView(
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

    getElement("uploadprofilepic").onchange = (e) => {
        handleCropImageUpload(
            e,
            "profileImageData",
            "profilePicOutput",
            (croppedB64) => {
                getElement("uploadprofilepiclabel").innerHTML = "Selected";
                getElement("profilePicOutput").style.opacity = 1;
            }
        );
    };
}