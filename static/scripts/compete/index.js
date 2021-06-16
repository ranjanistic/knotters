const competitiontabcontent = document.querySelectorAll(".competitiontabcontent");

intializeTabsView(
  async (tabID) => {
    if (tabID == "competeactive") {
      return competitiontabcontent[0].innerHTML;
    }
    return competitiontabcontent[1].innerHTML;
  },
  "competitionstab",
  "compete-nav-tab",
  "positive",
  "primary",
  "ctabview"
);
