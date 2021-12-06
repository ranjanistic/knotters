let viewedSnaps = []

const viewers = getElements("snapshot-viewer");

const loadBrowseSnaps = async () => {
    let viewer = viewers.find(view=>view.innerHTML.trim()=="")
    if(!viewer){
       viewer = viewers[viewers.length - 1]
    }
    let snapdata = await postRequest(setUrlParams(URLS.BROWSER,"project-snapshots"), {
       excludeIDs: viewedSnaps
    });
    if(!snapdata) return false;
    if(snapdata.code === code.OK && snapdata.snapIDs.length) {
       viewedSnaps = viewedSnaps.concat(snapdata.snapIDs)
       viewer.innerHTML += snapdata.html
       return true
    }
   return false
}

if(viewers.length){
    (async()=>{
        let done = await loadBrowseSnaps();
        if(done) {
            window.addEventListener("scroll", async ()=>{
                if(done && document.body.scrollTop+document.body.offsetHeight+100 > viewers[0].offsetHeight){              
                    done = await loadBrowseSnaps();
                })
            }
        }
    })();
}
