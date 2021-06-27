const loadTabScript = (tabID) => {

};
initializeTabsView({
    onEachTab: async (tabID) => await getRequest(`${ROOT}/indexTab/${tabID}`),
    uniqueID: "competitionstab",
    tabsClass: "compete-nav-tab",
    onShowTab: loadTabScript,
});


// var values = ["hello", "bye"];
// var inputValues = ["morning", "night"];

// handleDropDowns("dropdown-box", "compete-dropdown", values);

// handleInputDropdowns(
//   "input-dropdown-box",
//   "compete-input-dropdown",
//   inputValues
// );
