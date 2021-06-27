let compdata = {};

if (isActive) {
    (async () => {
        const data = await postRequest(`${ROOT}/data/${compID}`);
        console.log(data)
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

const loadTabScript = (tabID) => {
    switch (tabID) {
        case "submission": {
            if(isActive){
                if(compdata.participated){
                    handleInputDropdowns({
                        dropdownID:"findPeople",
                        onInput:async({inputField,listContainer,createList})=>{
                            if(inputField.value){
                                listContainer.innerHTML = loaderHTML()
                                let data = await postRequest(`${ROOT}/people/${compID}/${inputField.value}`)
                                console.log(data)
                                if(data.code == "OK"){
                                    listContainer.innerHTML = ''
                                    createList([data.person])
                                } else {
                                    listContainer.innerHTML = 'No such person available.'
                                }
                            }
                        }
                    });
                } else {
                    
                }
            }
        }
    }
};

initializeTabsView({
    onEachTab: async (tabID) => {
        return await getRequest(`${ROOT}/competeTab/${compID}/${tabID}`);
    },
    uniqueID: "competetab",
    tabsClass: "side-nav-tab",
    activeTabClass: "active",
    onShowTab: loadTabScript,
});
