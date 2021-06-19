if (selfProject) {
    getElement("uploadprojectimage").onchange = (e) => {
        handleCropImageUpload(
            e,
            "projectimageData",
            "projectimageoutput",
            (croppedB64) => {
                getElement("uploadprojectimagelabel").innerHTML = "Selected";
                getElement("projectimageoutput").style.opacity = 1;
            }
        );
    };
}
