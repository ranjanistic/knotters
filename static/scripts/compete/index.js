initializeTabsView({
  onEachTab: async (tabID) => {
    return await getRequest(`${ROOT}/indexTab/${tabID}`);
  },
  uniqueID:"competitionstab",
  tabsClass:"compete-nav-tab"
});

// var values = ["hello", "bye"];
// var inputValues = ["morning", "night"];

// handleDropDowns("dropdown-box", "compete-dropdown", values);

// handleInputDropdowns(
//   "input-dropdown-box",
//   "compete-input-dropdown",
//   inputValues
// );
