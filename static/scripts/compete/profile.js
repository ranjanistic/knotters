
intializeTabsView(
    async (tabID) => {
        return await getRequest(`/competition/profiletab/${compID}/${tabID}`);
    },
    "competetab",
    "side-nav-tab",
    "active"
);

// function openSideTab(evt, tabName) {
//     var i, x, tablinks;
//     x = document.getElementsByClassName("tab");
//     for (i = 0; i < x.length; i++) {
//         x[i].style.display = "none";
//     }
//     tablinks = document.getElementsByClassName("side-nav-tab");
//     for (i = 0; i < x.length; i++) {
//         tablinks[i].className = tablinks[i].className.replace(" active", "");
//     }
//     document.getElementById(tabName).style.display = "block";
//     evt.currentTarget.className += " active";
// }

// /* ============== fetch competition api ================ */

// var sideNavTabs = document.querySelectorAll(".side-nav-tab");

// for (var n = 0; n < sideNavTabs.length; n++) {
//     sideNavTabs[n].addEventListener("click", getApiCompetition);
// }

// function getApiCompetition() {
//     openSpinner();
//     fetch("https://jsonplaceholder.typicode.com/users/1")
//         .then((response) => response.json())
//         .then((json) => {
//             console.log(json);
//             return json;
//         })
//         .then((response) => {
//             if (response) {
//                 hideSpinner();
//             }
//         })
//         .catch(handleErrorCompetition);
// }

// function handleErrorCompetition() {
//     hideSpinner();
//     var tabsCompete = document.querySelectorAll(
//         "#overview, #task, #guidelines, #submission"
//     );

//     for (var s = 0; s < tabsCompete.length; s++) {
//         tabsCompete[s].innerHTML =
//             "<h5>Failed to load data <br/><br/><button onclick='getApiCompetition()'>Try again</button></h5>";
//     }
// }

// /* ============= Responsive side Navbar =========== */

// var responsive = window.matchMedia("(max-width:768px)");

// function responsiveSidebar(e) {
//     if (e.matches) {
//         document.getElementById("sidebar").className = "w3-bar";
//         document.getElementById("sidebar").style =
//             "display:flex; justify-content: space-between";
//     } else {
//         document.getElementById("sidebar").className = "w3-bar-block";
//         document.getElementById("sidebar").style.display = "block";
//     }
// }

// responsive.addEventListener("change", responsiveSidebar);
// responsiveSidebar(responsive);
