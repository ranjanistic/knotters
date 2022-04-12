{% if not request.user.profile.is_manager %}
Swal.fire({
    title: "Only managers",
    html: "<h4>Core projects are currently reserved for management accounts only.</h4>",
}).then(() => {
    loaders();
    refer({ path: URLS.CREATE });
});
{% else %}
getElement("uploadprojectimage").onchange = (e) => {
    handleCropImageUpload(e, "projectimagedata", "projectimageoutput", (_) => {
        getElement("uploadprojectimagelabel").innerHTML = "Selected";
    });
};
getElements("create-project-input").forEach((element) => {
    if (!Array.from(element.classList).includes("no-retain")) {
        element.value = sessionStorage.getItem(
            `create-coreproject-input-${element.id || element.name}`
        );
        element.addEventListener("input", (e) => {
            sessionStorage.setItem(
                `create-coreproject-input-${element.id || element.name}`,
                element.value
            );
        });
    }
});

getElement("projectcodename").oninput = async (e) => {
    let nickname = String(e.target.value).toLowerCase().trim();
    nickname = nickname.replace(/[^a-z0-9\-]/g, "-").split('-').filter((k)=>k.length).join('-');
    if (!nickname) return;
    e.target.value = nickname;
};

getElement("projectcodename").onchange = async (e) => {
    let nickname = String(e.target.value).toLowerCase().trim();
    nickname = nickname.replace(/[^a-z0-9\-]/g, "-").split('-').filter((k)=>k.length).join('-');
    if (!nickname) return;
    e.target.value = nickname;
    const data = await postRequest(
        setUrlParams(URLS.CREATEVALIDATEFIELD, "codename"),
        { codename:nickname }
    );
    if (!data) return;
    if (data.code !== code.OK) return error(data.error);
    return message(`'${String(e.target.value).trim()}' is available!`);
};
const choose_moderator_views = getElement("choose_moderator_views");
const modSearchInput = getElement("choose_moderator_search_input");
hide(choose_moderator_views);
const searchoninput = async (_) => {
    if (!modSearchInput.value.trim()) return;
    const data = await postRequest2({
        path: URLS.Management.MODSEARCH,
        data: {
            query: modSearchInput.value.trim(),
            internalOnly: false,
        },
    });
    if (!data) return;
    if (data.mod) {
        setHtmlContent(
            getElement("choose_moderator_search_output"),
            `<button class="primary" type="button" id="mod-search-output-button"><img src="${data.mod.dp}" class="circle" />${data.mod.name}</button>`,
            () => {
                getElement("mod-search-output-button").onclick = (_) => {
                    modSearchInput.oninput = null;
                    getElement("coreproject_moderator_id").value = data.mod.id;
                    getElement("choose_moderator_search_output").innerHTML = "";
                    setHtmlContent(
                        getElement("choose_moderator_selected_output"),
                        `Selected: <button class="accent" type="button" id="mod-selected-button" data-icon="close"><img src="${data.mod.dp}" class="circle" /> ${data.mod.name}</button>`,
                        () => {
                            getElement("mod-selected-button").onclick = (_) => {
                                getElement("coreproject_moderator_id").value =
                                    "";
                                getElement(
                                    "choose_moderator_selected_output"
                                ).innerHTML = "";
                                modSearchInput.oninput = searchoninput;
                            };
                        }
                    );
                };
            }
        );
    } else {
        getElement("choose_moderator_search_output").innerHTML =
            "No results found";
    }
};
Array.from(document.getElementsByName("moderator_type_radio")).forEach(
    (radio) => {
        radio.onchange = (_) => {
            if (radio.id == "chosen_moderator") {
                modSearchInput.oninput = searchoninput;
                visible(choose_moderator_views, radio.checked);
                getElement("coreproject_random_moderator").checked = false;
                getElement("coreproject_internal_moderator").checked = false;
            } else {
                hide(choose_moderator_views);
                getElement("coreproject_moderator_id").value = "";
                getElement("choose_moderator_selected_output").innerHTML = "";
                if (radio.id === "random_moderator") {
                    getElement("coreproject_random_moderator").checked = true;
                    getElement(
                        "coreproject_internal_moderator"
                    ).checked = false;
                } else {
                    getElement("coreproject_internal_moderator").checked = true;
                    getElement("coreproject_random_moderator").checked = false;
                }
            }
        };
    }
);

getElements("existing-license-button").forEach((lic) => {
    const liconclick = (_) => {
        getElements("existing-license-button").forEach((_lic) => {
            if (_lic.id != lic.id) {
                _lic.classList.remove("positive");
                _lic.classList.add("primary");
            } else {
                _lic.classList.add("positive");
                _lic.classList.remove("primary");
            }
        });
        getElement("coreproject_license_name").onchange = null;
        getElement("coreproject_license_about").onchange = null;
        getElement("coreproject_license_content").onchange = null;
        lic.onclick = (_) => {
            getElement("coreproject_license_id").value = "";
            getElements("existing-license-button").forEach((lic) => {
                lic.classList.remove("positive");
                lic.classList.add("primary");
            });
            getElement("coreproject_license_name").value = "";
            getElement("coreproject_license_about").value = "";
            getElement("coreproject_license_content").value = "";
            getElement("coreproject_license_name").disabled = false;
            getElement("coreproject_license_about").disabled = false;
            getElement("coreproject_license_content").disabled = false;
            lic.onclick = liconclick;
        };
        getElement("coreproject_license_id").value = lic.id;
        getElement("coreproject_license_name").value = lic.dataset.name;
        getElement("coreproject_license_about").value = lic.dataset.about;
        getElement("coreproject_license_content").value = lic.dataset.content;
        getElement("coreproject_license_name").disabled = true;
        getElement("coreproject_license_about").disabled = true;
        getElement("coreproject_license_content").disabled = true;
    };
    lic.onclick = liconclick;
});
getElement("coreproject_license_name").disabled = false;
getElement("coreproject_license_about").disabled = false;
getElement("coreproject_license_content").disabled = false;
{% endif %}
