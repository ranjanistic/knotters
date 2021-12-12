const loadBrowseSnaps = async (excludeIDs=[]) => {
    const viewers = getElements("snapshot-viewer");
    let viewer = viewers.find(view=>(view.innerHTML.trim()==""))
    if(!viewer){
       viewer = viewers[viewers.length - 1]
    }
    let snapdata = await postRequest(setUrlParams(URLS.BROWSER,"project-snapshots"), {
        excludeIDs,
    });
    if(!snapdata) return false;
    if(snapdata.code === code.OK && snapdata.snapIDs.length) {
        setHtmlContent(viewer, viewer.innerHTML + snapdata.html);
       return snapdata.snapIDs
    }
   return false
}

const loadSnapshotScroller = async () => {
    const viewers = getElements("snapshot-viewer");
    if(viewers.length){
        let viewedSnaps = []
        let done = await loadBrowseSnaps();
        if(done) {
            viewedSnaps = viewedSnaps.concat(done)
            let options = {
                root: null,
                rootMargins: "0px",
                threshold: 0.5
            };
            const observer = new IntersectionObserver(async (entries)=>{
                if (entries[0].isIntersecting && done) {
                    viewedSnaps = viewedSnaps.concat(done);    
                    done = await loadBrowseSnaps(viewedSnaps);
                    console.log("Snapshot");
                }
            }, options);
            observer.observe(document.querySelector(`#snap-${viewedSnaps[viewedSnaps.length-1].replaceAll('-','')}`));
        }
    }
}

const showSnapshotMoreBtn = () => {
    document.getElementById('id01').style.display = 'flex';
}

window.onclick = (event) => {
    if (event.target == document.getElementById('id01')) {
        document.getElementById('id01').style.display = "none";
    }
}