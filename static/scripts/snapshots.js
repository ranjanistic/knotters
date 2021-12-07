let dataJson, data, IDs=[],callTime=0,IDlength=0;
const getSnapshot = async () => {
    url = setUrlParams(URLS.BROWSER, "project-snapshots");
    if (callTime==3) {
        dataJson = await postRequest(url);
        data = dataJson.html;   
    } else {
        dataJson = await postRequest(url, { excludeIDs: IDs });
        data=+dataJson.html;
        console.log("dataJSON=>",dataJson)
    }
    IDs = IDs.concat(dataJson.snapIDs);
    
    // console.log("Snapshot data=>", data);
    if (!data) {
        console.log("Snapshot Error")
    } else {
        document.getElementById("browser-snapshots").innerHTML = data;
        const ids = [...document.querySelectorAll("#browser-snapshots [id]")].map(({id})=>id);
        const element = document.querySelector(`#${ids[callTime]}`);
        // console.log("element =>", element);
        // console.log("Time=>", callTime);
        document.addEventListener('scroll', () => {
        const clientHeight = document.documentElement.clientHeight;
        const elementSectionY = element.getBoundingClientRect().y;
        const elementHeight = element.getBoundingClientRect().height;
        // console.log("element height=>", elementSectionY);
        if (clientHeight > elementSectionY + elementHeight * (2 / 3) && (callTime%3)==0) {
            console.log("Post Request Call=>",callTime);
            callTime=callTime+3;
            getSnapshot();
        }
        });
        
        // window.addEventListener('scroll', () => {
        //     if ((window.scrollY + window.innerHeight) > document.documentElement.scrollHeight) {
        //         console.log("Request Call");
        //         getSnapshot();
        //     }
        // })

    }
};


document.addEventListener('DOMContentLoaded', () => {
    
});

const handleIntersect = (entries) => {
    if (entries[0].isIntersecting) {
        // callTime += IDlength;
        console.log("Intersecting callTime=>", callTime);
        getSnap();
    }
}

const getSnap = async () => {
    url = setUrlParams(URLS.BROWSER, "project-snapshots");
    if (callTime==0) {
        dataJson = await postRequest(url);
        data = dataJson.html;
        IDlength = dataJson.snapIDs.length - 1;
        callTime = IDlength;
    } else {
        dataJson = await postRequest(url, { excludeIDs: IDs });
        data = +dataJson.html;
        IDlength=dataJson.snapIDs.length;
        callTime += IDlength;
        // console.log("dataCallTime=>",callTime)
    }
    IDs = IDs.concat(dataJson.snapIDs);
    console.log("Snapshot data id=>", IDs);
    
    if (!data) {
        callTime = -1;
        console.log("Snapshot Error");
        return;
    } else {     
        let main = document.getElementById("browser-snapshots");
        main.innerHTML=data;
        const ids = [...document.querySelectorAll("#browser-snapshots [id]")].map(({id})=>id);
        console.log("Snapshot Data=>",callTime);
        let options = {
            root: null,
            rootMargins: "0px",
            threshold: 0.5
        };
        const observer = new IntersectionObserver(handleIntersect, options);
        observer.observe(document.querySelector(`#${ids[callTime]}`));
    }
}