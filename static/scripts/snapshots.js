const getSnapshot = async () => {
        url ="http://127.0.0.1:8000/projects/snapshots/e22b4c0deb6c4bd695fe50bccab35e62/0/10/";
    const data = await getRequest(url, { id: [] });
    console.log("Snapshot Error=>",data);
    if (!data) {
        console.log("Snapshot Error")    
    } else {
        document.getElementById("browser-snapshots").innerHTML = data;
        const ids = [...document.querySelectorAll("#browser-snapshots [id]")].map(({id})=>id);
        console.log("Snapshot=>", ids);
        let callTime = 0;
        const element = document.querySelector(`a#${ids[4]}`);
        document.addEventListener('scroll', () => {
        const clientHeight = document.documentElement.clientHeight;
        const elementSectionY = element.getBoundingClientRect().y;
        const elementHeight = element.getBoundingClientRect().height;
        if (clientHeight > elementSectionY + elementHeight * (2 / 3) && callTime == 0) {
            console.log('Get Request Call');
            callTime++;
        }
        });

    }
};
