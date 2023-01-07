getElement("resume-file").onchange = async (e) => {
    const file = e.target.files[0];
    if (file.size / 1024 / 1024 > 10) {
        error(STRING.file_too_large_10M);
        return;
    }
    getElement("resume").value = await convertFileToBase64(file);
    getElement("resume-name").value = file.name;

};
