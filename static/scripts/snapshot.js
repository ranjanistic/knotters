const loadBrowseSnaps = async (excludeIDs=[]) => {
    const viewers = getElements("snapshot-viewer");
    let viewer = viewers.find(view=>(view.innerHTML.trim()==""))
    if(!viewer){
       viewer = viewers[viewers.length - 1]
    }
    let snapdata = await postRequest(setUrlParams(URLS.BROWSER,"project-snapshots"), {
       excludeIDs
    });
    if(!snapdata) return false;
    if(snapdata.code === code.OK && snapdata.snapIDs.length) {
       viewer.innerHTML += snapdata.html
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
            window.addEventListener("scroll", async ()=>{
                if(done && (document.body.scrollTop+document.body.offsetHeight+100) > viewers[0].offsetHeight){
                    viewedSnaps = viewedSnaps.concat(done);    
                    done = await loadBrowseSnaps(viewedSnaps);
                }
            });
        }
    }
}
