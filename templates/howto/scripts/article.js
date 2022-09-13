const self = "{{ self }}"==='True'
const isRater = "{{isRater}}"==='True'
const articleID = "{{ article.id }}"
const canEdit = "{{ article.isEditable }}"==="True"

const loadArticle = async() => {
    const data = await getRequest2({path : 
        setUrlParams(URLS.RENDER_ARTICLE, "{{article.get_nickname}}")}
        )
    setHtmlContent(getElement("article-head"), data.article_head)
    setHtmlContent(getElement("sections"), data.sections)
    afterLoad();
}

loadArticle();

const paragraph_content = 
`<div class="w3-row w3-padding">
    <div class="temp-paragraphs">
        <textarea class="wide paragraph" name='paragraph' rows="3" placeholder="paragraph"></textarea>
    </div>
</div>
<br />`

const image_content = `<input hidden id="upload-image" type='file' accept="image/png, image/jpg, image/jpeg"/>`

const video_content = `<input hidden id="upload-video" type='file' accept="video/mp4, video/ogg"/>`

const createImageSection = async(imageData) => {
    const resp = await postRequest2({
        path: setUrlParams(URLS.SECTION, articleID, 'create'),
        data :
        {
            image : imageData,
        }
    });
    if (resp.code === code.OK) 
    {
        await refreshSectionEdit();
        return
    }
    error(resp.error);
}

const createVideoSection = async(videoData) => {
    const resp = await postRequest2({
        path: setUrlParams(URLS.SECTION, articleID, 'create'),
        data :
        {
            video : videoData,
        }
    });
    if (resp.code === code.OK) 
    {
        await refreshSectionEdit();
        return
    }
    error(resp.error);
}

const handleImageSectionCreation = () => {
    appendHtmlContent(getElement("section-edit-inputs"), image_content)
    const upload_image = getElement("upload-image")
    upload_image.click()
    upload_image.onchange = (e) => {
            handleCropImageUpload(
                e,
                `imageData`,
                `imageOutput`,
                (croppedB64) => {
                    createImageSection(croppedB64);
                },
                true,
                false
            )
        };
    upload_image.outerHTML = ""
    }

const handleVideoSectionCreation = () => {
    appendHtmlContent(getElement("section-edit-inputs"), video_content)
    const upload_video = getElement("upload-video")
    upload_video.click()
    upload_video.onchange = (e) => {
            handleVideoUpload(
                e,
                `videoData`,
                `videoOutput`,
                (videoData) => {
                    createVideoSection(videoData)
                },
                false
            )
        };
    upload_video.outerHTML = ""
}

const handleSectionCreation = () => {
    appendHtmlContent(getElement("section-edit-inputs"), paragraph_content)
    afterLoad();
    getElements(`temp-paragraphs`).forEach((temp_element) => {
        temp_element.onchange = async() => {
            let paragraph = temp_element.getElementsByClassName("paragraph")[0].value
            const resp = await postRequest2({
                path: setUrlParams(URLS.SECTION, articleID, 'create'),
                data :
                {
                    paragraph : paragraph,
                }
            });
            if (resp.code === code.OK) 
            {
                appendHtmlContent(getElement("sidenav-edit"), 
                `<div class="w3-row">
                    <div class="w3-col s10 m10 l10">
                        <div class="section-edit" sectionid="${resp.sectionID}">
                            <input type="text" class="primary w3-input subheading" name="subheading" placeholder="Subheading" value="Untitled Section"/>
                        </div>
                    </div>
                    <div class="w3-col s2 m2 l2">
                        <button class="small w3-right negative" id='delete-section-${resp.sectionID}' data-icon='delete'></button>  
                    </div>
                </div>   
                <br />`)
                appendHtmlContent(getElement("sidenav2-edit"), 
                `<div class="w3-row">
                    <div class="w3-col s10 m10 l10">
                        <div class="section-edit section-elements" sectionid="${resp.sectionID}">
                            <input type="text" class="primary w3-input subheading" name="subheading" placeholder="Subheading" value="Untitled Section"/>
                        </div>
                    </div>
                    <div class="w3-col s2 m2 l2">
                        <button class="small w3-right negative" id='delete-section-${resp.sectionID}' data-icon='delete'></button>  
                    </div>   
                </div>
                <br />`)
                temp_element.classList.remove(`temp-paragraphs`)
                temp_element.classList.add("section-edit") 
                temp_element.setAttribute("sectionid", resp.sectionID)
                temp_element.getElementsByTagName("textarea")[0].innerHTML = paragraph
                temp_element.onchange="";
                afterLoad();
                return
            }
            error(resp.error);
        }
    })
}

const refreshSectionEdit = async() => {
    const data = await getRequest2({path : 
        setUrlParams(URLS.RENDER_ARTICLE, "{{article.get_nickname}}")}
        )
    setHtmlContent(getElement("sections"), data.sections)
    hide(getElement("sidenav-view"))
    show(getElement("sidenav-edit"))
    hide(getElement("sidenav2-view"))
    show(getElement("sidenav2-edit"))
    hide(getElement("section-body-view"))
    show(getElement("section-body-edit"))
    afterLoad();
}

const handleSectionDelete = async(sectionID) => {
    await Swal.fire({
        title: `${NegativeText("Delete Section")}`,
        html: `<h5>This action is irreversible. Proceed with caution.</h5>`,
        showConfirmButton: false,
        showDenyButton: true,
        showCancelButton: true,
        cancelButtonText: "Go back",
        denyButtonText: "Delete Section",
    }).then(async (result) => {
        if (result.isDenied) {
            const resp = await postRequest2({
                path: setUrlParams(URLS.SECTION, articleID, 'remove'),
                data :
                {
                    sectionid : sectionID
                }
            });
            if (resp.code === code.OK) 
            {
                await refreshSectionEdit();
                success(STRING.section_deleted)
                return
            }
            error(resp.error);
        };
    })
}

const afterLoad = () => {
    if (self && canEdit) {
        getElement("edit-article").onclick = () => {
            heading_height = Math.max(getElement("heading-view").clientHeight, 100)
            subheading_height = Math.max(getElement("subheading-view").clientHeight, 100)
            getElement("heading").style.height =  heading_height + "px"
            getElement("subheading").style.height =  subheading_height + "px"
            hide(getElement("article-head-view"))
            show(getElement("article-head-edit"))
            hide(getElement("sidenav-view"))
            show(getElement("sidenav-edit"))
            hide(getElement("sidenav2-view"))
            show(getElement("sidenav2-edit"))
            hide(getElement("section-body-view"))
            show(getElement("section-body-edit"))
            hide(getElement("edit-article"))
            show(getElement("save-article"))
        }

        getElement("save-article").onclick = async() => {
            loadArticle();
            show(getElement("edit-article"))
            hide(getElement("save-article"))
        }

        let heading = getElement("heading")
        let subheading = getElement("subheading")
        heading.onchange = (async() => {
            const resp = await postRequest2({
                path: setUrlParams(URLS.SAVE, "{{article.get_nickname}}"),
                data :
                {
                    heading : heading.value,
                    subheading : subheading.value,
                }
            });
            if (resp.code === code.OK) 
            {
                message("saving")
                return
            }
            error(resp.error);
        })

        subheading.onchange = (async() => {
            const resp = await postRequest2({
                path: setUrlParams(URLS.SAVE, "{{article.get_nickname}}"),
                data :
                {
                    heading : heading.value,
                    subheading : subheading.value,
                }
            });
            if (resp.code === code.OK) 
            {
                message("saving")
                return
            }
            error(resp.error);
        })
        
        getElements("section-edit").forEach((section) => {
            section.addEventListener('change', async() =>   {
                let sectionID = section.getAttribute("sectionid")
                let subheading = section.getElementsByClassName("subheading")
                subheading = subheading.length>0?subheading[0].value:""
                let paragraph = section.getElementsByClassName("paragraph")
                paragraph = paragraph.length>0?paragraph[0].value:""
                let image = section.getElementsByClassName("image")
                image = image.length>0?image[0].value:""
                let video = section.getElementsByClassName("video")
                video = video.length>0?video[0].value:""
                const resp = await postRequest2({
                    path: setUrlParams(URLS.SECTION, articleID, 'update'),
                    data :
                    {
                        sectionid : sectionID,
                        subheading : subheading,
                        paragraph : paragraph,
                        image : image,
                        video : video,
                    }
                });
                if (resp.code === code.OK) 
                {
                    if(paragraph)
                        section.getElementsByClassName("paragraph")[0].innerHTML = paragraph
                    message("saving")
                    return
                }
                error(resp.error);
            })
        })

        getElements("section-elements").forEach((section) => {
            let sectionID = section.getAttribute("sectionid")
            if(section.getAttribute("hasImage")==="true")
            {
                getElement(`section-file-${sectionID}`).onchange = (e) => {
                    handleCropImageUpload(
                        e,
                        `imageData-${sectionID}`,
                        `imageOutput-${sectionID}`,
                        (croppedB64) => {
                            hide(getElement(`add-image-view-${sectionID}`))
                            getElement(`imageOutput-${sectionID}`).style.opacity = '1'
                            getElement(`event-${sectionID}`).click()
                        },
                        true
                    );
                };
            }

            document.querySelectorAll(`#delete-section-${sectionID}`).forEach((delete_button) => {
                delete_button.onclick = () => {
                    handleSectionDelete(sectionID)
                }
            })

        })

        getElement("add-paragraph").onclick = () => {
            handleSectionCreation("paragraph");
        }

        getElement("add-image").onclick = () => {
            handleImageSectionCreation();
        }

        getElement("add-video").onclick = () => {
            handleVideoSectionCreation();
        }

        getElements("section-edit").forEach((section) => {
            section.addEventListener('change', async() =>   {
            })
        })
        document.querySelectorAll("#deleteArticle").forEach((delete_button) => {
            delete_button.addEventListener('click', async(_) => {
                await Swal.fire({
                    title: `${NegativeText("Delete Article")}`,
                    html: `<h5>This action is irreversible. Proceed with caution.</h5>`,
                    showConfirmButton: false,
                    showDenyButton: true,
                    showCancelButton: true,
                    cancelButtonText: "Go back",
                    denyButtonText: "Delete Article",
                }).then(async (result) => {
                    if (result.isDenied) {
                        const resp = await postRequest2({
                            path: setUrlParams(URLS.DELETE, articleID),
                            data: {
                                confirm: true
                            },
                        });
                        if (resp.code === code.OK) 
                        {
                            relocate({path: URLS.HOWTO, query: {
                                s: STRING.article_deleted
                            }})
                            return
                        }
                        error(resp.error);
                    };
                })
            })
        })

    {% if article.is_draft %}
            getElement("publishArticle").onclick = async(_) => {
                await Swal.fire({
                    title: `Publish Article`,
                    html: `<h5>Article cannot be drafted back once published. You will be allowed to edit the article for a period of 7 days after publishing the article.</h5>`,
                    showConfirmButton: true,
                    showDenyButton: false,
                    showCancelButton: true,
                    cancelButtonText: "Go back",
                    confirmButtonText: "Publish Article",
                }).then(async (result) => {
                    if (result.isConfirmed) {
                        const resp = await postRequest2({
                            path: setUrlParams(URLS.Howto.PUBLISH, articleID)
                        })
                        if(resp.code === code.OK)
                        {
                            relocate({query:{
                                s: STRING.article_published
                            }})
                            return
                        }
                        error(resp.error);
                    }
                })
            }
        {% endif %}

        const loadExistingTags = () => {
            initializeMultiSelector({
                candidateClass: "tag-existing",
                selectedClass: "negative",
                deselectedClass: "primary negative-text",
                onSelect: (btn) => {
                    if (!getElement("removetagIDs").value.includes(btn.id))
                        getElement("removetagIDs").value += getElement(
                            "removetagIDs"
                        ).value
                            ? "," + btn.id
                            : btn.id;
                    return true;
                },
                onDeselect: (btn) => {
                    let addtagids = getElement("addtagIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let addtags = getElement("addtags")
                        .value.split(",")
                        .filter((x) => x);
                    let addtaglen = addtagids.length + addtags.length;
                    let remtagids = getElement("removetagIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let remtaglen = remtagids.length;
                    if (
                        getElements("tag-existing").length -
                            remtaglen +
                            addtaglen ===
                        5
                    ) {
                        error(STRING.upto_5_tags_allowed);
                        return false;
                    }

                    getElement("removetagIDs").value = getElement(
                        "removetagIDs"
                    )
                        .value.replaceAll(btn.id, "")
                        .split(",")
                        .filter((x) => x)
                        .join(",");
                    return true;
                },
            });
        };
        const loadNewTags = () => {
            initializeMultiSelector({
                candidateClass: "tag-new",
                selectedClass: "positive",
                deselectedClass: "primary",
                onSelect: (btn) => {
                    let addtagids = getElement("addtagIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let addtags = getElement("addtags")
                        .value.split(",")
                        .filter((x) => x);
                    let addtaglen = addtagids.length + addtags.length;
                    let remtagids = getElement("removetagIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let remtaglen = remtagids.length;

                    if (
                        getElements("tag-existing").length -
                            remtaglen +
                            addtaglen ===
                        5
                    ) {
                        error(STRING.upto_5_tags_allowed);
                        return false;
                    }
                    if (btn.classList.contains("tag-name")) {
                        if (!getElement("addtags").value.includes(btn.id))
                            getElement("addtags").value += getElement("addtags")
                                .value
                                ? "," + btn.id
                                : btn.id;
                    } else {
                        if (!getElement("addtagIDs").value.includes(btn.id))
                            getElement("addtagIDs").value += getElement(
                                "addtagIDs"
                            ).value
                                ? "," + btn.id
                                : btn.id;
                    }
                    return true;
                },
                onDeselect: (btn) => {
                    if (!btn.classList.contains("tag-name")) {
                        getElement("addtagIDs").value = getElement("addtagIDs")
                            .value.replaceAll(btn.id, "")
                            .split(",")
                            .filter((x) => x)
                            .join(",");
                    } else {
                        getElement("addtags").value = getElement("addtags")
                            .value.replaceAll(btn.id, "")
                            .split(",")
                            .filter((x) => x)
                            .join(",");
                    }
                    return true;
                },
            });
        };
        let lasttagquery = "";
        getElement("tag-search-input").oninput = async (e) => {
            if (!e.target.value.trim()) return;
            if (e.target.value.length != lasttagquery.length) {
                if (e.target.value.length < lasttagquery.length) {
                    lasttagquery = e.target.value;
                    return;
                } else {
                    lasttagquery = e.target.value;
                }
            }
            getElement("tags-viewer-new").innerHTML = "";
            const data = await postRequest2({
                path: setUrlParams(URLS.SEARCH_TAGS, articleID),
                data: {
                    query: e.target.value,
                },
            });
            if (!data) return;
            if (data.code === code.OK) {
                let buttons = [];
                data.tags.forEach((tag) => {
                    buttons.push(
                        `<button type="button" class="small ${
                            getElement("addtagIDs").value.includes(tag.id)
                                ? "positive"
                                : "primary"
                        } tag-new" id="${tag.id}">${Icon("add")}${
                            tag.name
                        }</button>`
                    );
                });
                if (buttons.length) {
                    getElement("tags-viewer-new").innerHTML = buttons.join("");
                    loadNewTags();
                    loadExistingTags();
                } else {
                    buttons.push(
                        `<button type="button" class="small ${
                            getElement("addtags").value.includes(e.target.value)
                                ? "positive"
                                : "primary"
                        } tag-new tag-name" id="${e.target.value}">${Icon(
                            "add"
                        )}${e.target.value}</button>`
                    );
                    getElement("tags-viewer-new").innerHTML = buttons.join("");
                    loadNewTags();
                    loadExistingTags();
                }
            } else {
                error(data.error);
            }
        };
        loadExistingTags();

        getElement("save-edit-articletags").onclick = async () => {
            var obj = getFormDataById("edit-tag-inputs");
            var resp = await postRequest(
                setUrlParams(URLS.EDIT_TAGS, articleID),
                {
                    addtagIDs: obj.addtagIDs.split(",").filter((str) => str),
                    addtags: obj.addtags.split(",").filter((str) => str),
                    removetagIDs: obj.removetagIDs
                        .split(",")
                        .filter((str) => str),
                }
            );
            if (resp.code === code.OK) {
                subLoader();
                return window.location.reload();
            }
            error(resp.error);
        };

        const loadExistingTopics = () => {
            initializeMultiSelector({
                candidateClass: "topic-existing",
                selectedClass: "negative",
                deselectedClass: "primary negative-text",
                onSelect: (btn) => {
                    const remtopIDselem = getElement("removetopicIDs");
                    if (!remtopIDselem.value.includes(btn.id))
                        remtopIDselem.value += remtopIDselem.value
                            ? "," + btn.id
                            : btn.id;
                    return true;
                },
                onDeselect: (btn) => {
                    let addtopids = getElement("addtopicIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let addtops = getElement("addtopics")
                        .value.split(",")
                        .filter((x) => x);
                    let addtoplen = addtopids.length + addtops.length;

                    let remtopids = getElement("removetopicIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let remtoplen = remtopids.length;

                    if (
                        getElements("topic-existing").length -
                            remtoplen +
                            addtoplen ===
                        3
                    ) {
                        error(STRING.upto_3_topics_allowed);
                        return false;
                    }
                    getElement("removetopicIDs").value = getElement(
                        "removetopicIDs"
                    )
                        .value.replaceAll(btn.id, "")
                        .split(",")
                        .filter((x) => x)
                        .join(",");
                    return true;
                },
            });
        };
        const loadNewTopics = () => {
            initializeMultiSelector({
                candidateClass: "topic-new",
                selectedClass: "positive",
                deselectedClass: "primary",
                onSelect: (btn) => {
                    let addtopids = getElement("addtopicIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let addtops = getElement("addtopics")
                        .value.split(",")
                        .filter((x) => x);
                    let addtoplen = addtopids.length + addtops.length;

                    let remtopids = getElement("removetopicIDs")
                        .value.split(",")
                        .filter((x) => x);
                    let remtoplen = remtopids.length;
                    if (
                        getElements("topic-existing").length -
                            remtoplen +
                            addtoplen ===
                            3
                    ) {
                        error(STRING.upto_3_topics_allowed);
                        return false;
                    }
                    if (btn.classList.contains("topic-name")) {
                        if (!getElement("addtopics").value.includes(btn.id))
                            getElement("addtopics").value += getElement(
                                "addtopics"
                            ).value
                                ? "," + btn.id
                                : btn.id;
                    } else {
                        if (!getElement("addtopicIDs").value.includes(btn.id))
                            getElement("addtopicIDs").value += getElement(
                                "addtopicIDs"
                            ).value
                                ? "," + btn.id
                                : btn.id;
                    }
                    return true;
                },
                onDeselect: (btn) => {
                    if (!btn.classList.contains("topic-name")) {
                        getElement("addtopicIDs").value = getElement(
                            "addtopicIDs"
                        )
                            .value.replaceAll(btn.id, "")
                            .split(",")
                            .filter((x) => x)
                            .join(",");
                    } else {
                        getElement("addtopics").value = getElement("addtopics")
                            .value.replaceAll(btn.id, "")
                            .split(",")
                            .filter((x) => x)
                            .join(",");
                    }
                    return true;
                },
            });
        };
        let lastquery = "";
        getElement("topic-search-input").oninput = async (e) => {
            if (!e.target.value.trim()) return;
            if (e.target.value.length != lastquery.length) {
                if (e.target.value.length < lastquery.length) {
                    lastquery = e.target.value;
                    return;
                } else {
                    lastquery = e.target.value;
                }
            }
            getElement("topics-viewer-new").innerHTML = "";
            const data = await postRequest2({
                path: setUrlParams(URLS.SEARCH_TOPICS, articleID),
                data: {
                    query: e.target.value,
                },
            });
            if (!data) return;
            if (data.code === code.OK) {
                let buttons = [];
                data.topics.forEach((topic) => {
                    buttons.push(
                        `<button type="button" class="${
                            getElement("addtopicIDs").value.includes(topic.id)
                                ? "positive"
                                : "primary"
                        } topic-new" id="${topic.id}">${Icon("add")}${
                            topic.name
                        }</button>`
                    );
                });
                if (buttons.length) {
                    getElement("topics-viewer-new").innerHTML =
                        buttons.join("");
                    loadNewTopics();
                    loadExistingTopics();
                } else {
                    buttons.push(
                        `<button type="button" class="${
                            getElement("addtopics").value.includes(
                                e.target.value
                            )
                                ? "positive"
                                : "primary"
                        } topic-new topic-name" id="${e.target.value}">${Icon(
                            "add"
                        )}${e.target.value}</button>`
                    );
                    getElement("topics-viewer-new").innerHTML =
                        buttons.join("");
                    loadNewTopics();
                    loadExistingTopics();
                }
            } else {
                error(data.error);
            }
        };
        loadExistingTopics();
        getElement("save-edit-articletopics").onclick = async () => {
            const obj = getFormDataById("edit-article-topics-form");
            const resp = await postRequest2({
                path: setUrlParams(URLS.EDIT_TOPICS, articleID),
                data: {
                    addtopicIDs: obj.addtopicIDs.split(",").filter((x) => x),
                    addtopics: obj.addtopics.split(",").filter((x) => x),
                    removetopicIDs: obj.removetopicIDs
                        .split(",")
                        .filter((x) => x),
                },
            });
            if (resp.code === code.OK) {
                subLoader();
                return window.location.reload();
            }
            error(resp.error);
        };
    }
    const userRatingScore = Number("{{userRatingScore}}")
    getElements('trigger-article-rating').forEach((triggerRate) => {
        let starStatus = {};
        triggerRate.onclick = () => {
            Swal.fire({
                title: `Rate this Article`,
                html:
                    `<div class="rate">
                    <input type="checkbox" id="rating1" class="rating-value"/><label for="rating1" class="half rating-star"></label>
                    <input type="checkbox" id="rating2" class="rating-value"/><label for="rating2"  class="rating-star"></label>
                    <input type="checkbox" id="rating3" class="rating-value"/><label for="rating3" class="half rating-star"></label>
                    <input type="checkbox" id="rating4" class="rating-value"/><label for="rating4"  class="rating-star"></label>
                    <input type="checkbox" id="rating5" class="rating-value"/><label for="rating5" class="half rating-star"></label>
                    <input type="checkbox" id="rating6" class="rating-value"/><label for="rating6"  class="rating-star"></label>
                    <input type="checkbox" id="rating7" class="rating-value"/><label for="rating7" class="half rating-star"></label>
                    <input type="checkbox" id="rating8" class="rating-value"/><label for="rating8"  class="rating-star"></label>
                    <input type="checkbox" id="rating9" class="rating-value"/><label for="rating9" class="half rating-star"></label> 
                    <input type="checkbox" id="rating10" class="rating-value"/><label for="rating10" class="rating-star"></label>
                </div>`,
                showDenyButton: isRater,
                showCancelButton: true,
                showConfirmButton: true,
                confirmButtonText: `Submit`,
                denyButtonText: `Remove Rating`,
                cancelButtonText: STRING.cancel,
                didOpen: () => {
                    let stars = getElements('rating-star');
                    stars.forEach((star, i) => {
                        if (i<userRatingScore){
                            star.classList.add("selected")
                            starStatus[star.getAttribute('for')] = true
                        }
                        star.onclick = () => {
                            stars.forEach((s, j) => {
                                if (j <= i) {
                                    s.classList.add("selected")
                                    starStatus[s.getAttribute('for')] = true
                                } else {
                                    s.classList.remove("selected")
                                    starStatus[s.getAttribute('for')] = false
                                }

                            })
                        }
                    })
                },
                preConfirm: () => {
                    const score =
                        Object.values(starStatus).filter((rv) => rv).length;
                    if (!score) {
                        error("Not a valid Rating");
                        return false;
                    }
                    return score;
                }
            }).then(async (result) => {
                if (result.isConfirmed) {
                    const data = await postRequest2({
                        path: setPathParams(URLS.RATING, articleID),
                        data: {
                            score: result.value, action: ACTIONS.CREATE
                        }
                    });
                    if (!data) return;
                    if (data.code === code.OK) {
                        return refresh({});
                    }
                    error(data.error);
                } else if (result.isDenied) {
                    const data = await postRequest2({
                        path: setPathParams(URLS.RATING, articleID),
                        data: {
                            action: ACTIONS.REMOVE
                        }
                    });
                    if (!data) return;
                    if (data.code === code.OK) {
                        return refresh({});
                    }
                    error(data.error);
                }

            })
        }
    })

    getElements('trigger-login-popup').forEach((triggerRate) => {
        triggerRate.onclick = () => {
            Swal.fire({
                title: `Login to rate`,
                showCancelButton: true,
                showConfirmButton: true,
                confirmButtonText: `Login`,
                cancelButtonText: STRING.cancel
            }).then(async (result) => {
                if (result.isConfirmed){
                    return refer({
                        path: URLS.Auth.LOGIN,
                        query: { next: window.location.pathname },
                    })
                }
            })
        }
    })

    getElement("show-admirations").onclick = async (_) => {
        Swal.fire({
            html: await getRequest2({
                path: setUrlParams(URLS.ADMIRATIONS, articleID),
            }),
            title: "<h4 class='positive-text'>Admirers</h4>",
        });
    };

    {% if sections %}
        getElement("opennav").onclick = () => {
            show(getElements("parent-sidenav")[0])
            hide(getElement("opennav"))
        }

        getElement("closenav").onclick = () => {
            hide(getElements("parent-sidenav")[0])
            show(getElement("opennav"))
        }

        window.addEventListener('mouseup', function (event) {
            let box = document.getElementById('sidenav-menu');
            if (!Array.from(box.getElementsByTagName("*")).includes(event.target)) {
                getElement("closenav").click()
            }
        });
    {% endif %}
}