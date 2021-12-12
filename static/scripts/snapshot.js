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
                }
            }, options);
            observer.observe(document.querySelector(`#snap-${viewedSnaps[viewedSnaps.length-1].replaceAll('-','')}`));
        }
    }
}
const showSnapshotMoreBtn = () => {
    document.getElementById('id01').style.display = 'flex';
}

window.addEventListener('click', (event) => {
    if (event.target == document.getElementById('id01')) {
        document.getElementById('id01').style.display = "none";
    }
});

const admireSnap = async (snapID) => {
    if(!snapID) return
    const admire = getElement(`snap-admire-${snapID}`).getAttribute("data-admires") == "0"
    const data = await postRequest(setUrlParams(URLS.Projects?URLS.Projects.TOGGLE_SNAP_ADMIRATION:URLS.TOGGLE_SNAP_ADMIRATION, snapID), {
        admire
    })
    if (data.code !== code.OK){
        return error(data.error)
    }
    getElement(`snap-admire-${snapID}`).setAttribute("data-admires", admire?1:0)
    getElement(`snap-admire-${snapID}`).classList[admire?'add':'remove']('positive')
    getElement(`snap-admire-${snapID}`).classList[admire?'remove':'add']('primary')
}

const reportSnap = async (snapID) => await violationReportDialog(URLS.Projects?URLS.Projects.REPORT_SNAPSHOT:URLS.REPORT_SNAPSHOT, { snapID }, "Snapshot", URLS.Projects?URLS.Projects.REPORT_CATEGORIES:URLS.REPORT_CATEGORIES)

const deleteSnap = (snapID,projectID) => {
    if(!snapID || !projectID) return
    alertify.confirm('Delete snapshot',
    "Are you sure you want to delete the snapshot?",
    ()=>{},
    ()=>{
        postRequest(
            setUrlParams(URLS.Projects?URLS.Projects.SNAPSHOT:URLS.SNAPSHOT, projectID, "remove"), {
                snapid:snapID,snapID
            }
        ).then((data) => {
            if (data.code === code.OK) {
                hideElement(`snap-${snapID}`)
                message(data.message);
            } else {
                error(data.error);
            }
        });
    }).set('labels', {ok:'No, go back', cancel:'Yes, delete'}).set('closable', false);
}
