const licenseviews = getElements("license-expand-view");
getElements("license-expand-action").map((act, a) => {
    act.onclick = (_) => {
        licenseviews[a].hidden = !licenseviews[a].hidden;
    };
});
