const loadTabScript = (tab) => {
    getElements("chart-view").forEach(async (chart) => {
        const myChart = new Chart(chart.getContext("2d"), {
            type: chart.getAttribute('data-type'),
            data: {
                labels: ["Red", "Blue", "Yellow", "Green", "Purple", "Orange"],
                datasets: [
                    {
                        label: "# of Votes",
                        data: [12, 19, 3, 5, 2, 3],
                        backgroundColor: [
                            "rgba(255, 99, 132, 0.2)",
                            "rgba(54, 162, 235, 0.2)",
                            "rgba(255, 206, 86, 0.2)",
                            "rgba(75, 192, 192, 0.2)",
                            "rgba(153, 102, 255, 0.2)",
                            "rgba(255, 159, 64, 0.2)",
                        ],
                        borderColor: [
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                        ],
                        borderWidth: 1,
                    },
                    {
                        label: "# of Votes",
                        data: [1, 12, 10, 15, 21, 13],
                        backgroundColor: [
                            "rgba(255, 99, 132, 0.2)",
                            "rgba(54, 162, 235, 0.2)",
                            "rgba(255, 206, 86, 0.2)",
                            "rgba(75, 192, 192, 0.2)",
                            "rgba(153, 102, 255, 0.2)",
                            "rgba(255, 159, 64, 0.2)",
                        ],
                        borderColor: [
                            "rgba(255, 99, 132, 1)",
                            "rgba(54, 162, 235, 1)",
                            "rgba(255, 206, 86, 1)",
                            "rgba(75, 192, 192, 1)",
                            "rgba(153, 102, 255, 1)",
                            "rgba(255, 159, 64, 1)",
                        ],
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                scales: {
                    y: {
                        beginAtZero: true,
                    },
                },
            },
        });
    });
};


initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest(`/people/profiletab/${userID}/${tab.id}`);
    },
    uniqueID:"profiletab",
    onShowTab: loadTabScript
});

if (selfProfile) {
    initializeTabsView({
        onEachTab: async (tab) => {
            return await getRequest(`/people/settingtab/${tab.id}`);
        },
        uniqueID:"profilestab",
        tabsClass:"set-tab",
        activeTabClass:"active",
        inactiveTabClass:"primary",
        viewID:"stabview",
        spinnerID:"sloader"
    });

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
