const self = "{{ self }}"==='True'
const isRater = "{{isRater}}"==='True'
const articleID = "{{ article.id }}"
const canEdit = "{{ article.isEditable }}"==="True"

const fetchSections = async() => {
    const data = await getRequest2({
        path: setUrlParams(URLS.RENDER_ARTICLE, "{{article.get_nickname}}")
    })
    console.log(data['sections'])
}
const article_content = {
    paragraph_input :
    `<div class="w3-row w3-padding temp-para-parent">
        <div class="temp-paragraphs">
            <textarea class="wide paragraph" name='paragraph' rows="3" placeholder="paragraph"></textarea>
        </div>
        <br />
    </div>`,

    image_input : `<input hidden id="upload-image" type='file' accept="image/png, image/jpg, image/jpeg"/>`,

    video_input : `<input hidden id="upload-video" type='file' accept="video/mp4, video/ogg"/>`,

    image_content : (sectionID, imageData) => {
        return `
        <div class="w3-row w3-padding section-content" sectionid="${ sectionID }">
            <input type='file' hidden id='section-file-${sectionID}' accept="image/png, image/jpg, image/jpeg"/>
            <div class="w3-center">
                <img class="primary w3-round-xlarge" src="${imageData}"  id="imageOutput-${sectionID}" style="opacity:0.5" />
            </div>
            <div class="dead-text w3-center w3-padding" id='add-image-view-${sectionID}'>
                <button type="button" class="small accent" data-icon="upload">
                    <label for="section-file-${sectionID}">Update Image</label>
                </button>
            </div>
            <input type="text" class="image" id='imageData-${sectionID}' name='image' hidden value="">
            <br />
        </div>`},

    video_content : (sectionID, videoData) => {
        return `
        <div class="w3-row w3-padding section-content" sectionid="${ sectionID }">
            <input type='file' hidden id='section-video-file-${sectionID}' accept="video/mp4, video/ogg"/>
            <div class="w3-center">
                <video class="w3-round-xlarge section-video" controls src="${videoData}" id="videoOutput-${sectionID}">
                    Your browser does not support the video playback.
                </video>
            </div>
            <div class="dead-text w3-center w3-padding" id='add-video-view-${sectionID}'>
                <button type="button" class="small accent" data-icon="upload">
                    <label for="section-video-file-${sectionID}">Update Video</label>
                </button>
            </div>
            <input type="text" class="video" id='videoData-${sectionID}' name='video' hidden value="">
            <br />
        </div>`},

    sidenav_mini_content: (sectionID) => {
        return `
        <div class="w3-row w3-margin-bottom section-content" sectionid="${ sectionID }">
            <div class="w3-col s10 m10 l10">
                <div class="section-edit" sectionid="${sectionID}">
                    <input id="${sectionID}-subheading" type="text" class="primary w3-input subheading" name="subheading" placeholder="Subheading" value="Untitled Section"/>
                </div>
            </div>
            <div class="w3-col s2 m2 l2">
                <button class="small w3-right negative" id='delete-section-${sectionID}' data-icon='delete'></button>  
            </div>
        </div>`},
    
    sidenav_content: (sectionID, hasImage=false, hasVideo=false) => {
        return `
        <div class="w3-row w3-margin-bottom section-content" sectionid="${ sectionID }">
            <div class="w3-col s10 m10 l10">
                <div class="section-edit section-elements" sectionid="${sectionID}" hasImage="${hasImage}" hasVideo="${hasVideo}">
                    <input id="${sectionID}-subheading-2" type="text" class="primary w3-input subheading" name="subheading" placeholder="Subheading" value="Untitled Section"/>
                </div>
            </div>
            <div class="w3-col s2 m2 l2">
                <button class="small w3-right negative" id='delete-section-${sectionID}' data-icon='delete'></button>  
            </div>  
        </div>`}
}

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
        appendHtmlContent(getElement("section-edit-inputs"), article_content.image_content(resp.sectionID, imageData))
        appendHtmlContent(getElement("sidenav-edit"), article_content.sidenav_mini_content(resp.sectionID))
        appendHtmlContent(getElement("sidenav2-edit"), article_content.sidenav_content(resp.sectionID, true, false))
        handleSectionUpdate()
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
        appendHtmlContent(getElement("section-edit-inputs"), article_content.video_content(resp.sectionID, videoData))
        appendHtmlContent(getElement("sidenav-edit"), article_content.sidenav_mini_content(resp.sectionID))
        appendHtmlContent(getElement("sidenav2-edit"), article_content.sidenav_content(resp.sectionID, false, true))
        handleSectionUpdate()
        return
    }
    error(resp.error);
}

const handleImageSectionCreation = () => {
    appendHtmlContent(getElement("section-edit-inputs"), article_content.image_input)
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
    appendHtmlContent(getElement("section-edit-inputs"), article_content.video_input)
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
    appendHtmlContent(getElement("section-edit-inputs"), article_content.paragraph_input)
    handleSectionUpdate();
    getElements(`temp-paragraphs`).forEach((temp_element) => {
        temp_element.oninput = () => {
            let paragarph = temp_element.getElementsByTagName('textarea')[0].value
            sessionStorage.setItem("paragarph-input", paragarph)
        }
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
                temp_element.classList.remove('temp-paragraphs')
                temp_element.classList.add('section-edit')
                temp_element.setAttribute('sectionid', resp.sectionID)
                let head_div = getElements('temp-para-parent')[0]
                head_div.classList.remove('temp-para-parent')
                head_div.classList.add('section-content')
                head_div.setAttribute('sectionid', resp.sectionID)
                let text_input = temp_element.getElementsByTagName('textarea')[0]
                text_input.innerHTML = paragraph
                text_input.setAttribute('id', `${resp.sectionID}-paragraph`) 
                appendHtmlContent(getElement("sidenav-edit"), article_content.sidenav_mini_content(resp.sectionID))
                appendHtmlContent(getElement("sidenav2-edit"), article_content.sidenav_content(resp.sectionID))
                sessionStorage.removeItem("paragarph-input")
                handleSectionUpdate();
                return
            }
            error(resp.error);
        }
    })
}

const handleSectionDeletion = async(sectionID) => {
    const res = await Swal.fire({
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
                success(STRING.section_deleted)
                return true
            }
            error(resp.error);
            return false
        };
    })
    return res
}

const updateSection = async({sectionID, subheading="", paragraph="", image="", video=""}) => {
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
        if(subheading) {
            getElement(`${sectionID}-subheading`).defaultValue = subheading
            getElement(`${sectionID}-subheading-2`).defaultValue = subheading
            sessionStorage.removeItem(`${sectionID}-subheading`)
        }
        if(paragraph) {
            getElement(`${sectionID}-paragraph`).innerHTML = paragraph
            sessionStorage.removeItem(`${sectionID}-paragraph`)
        }
        message("saving")
        return
    }
    error(resp.error);
}

let heading = getElement("heading")
let subheading = getElement("subheading")

const updateArticleHead = async() => {
    const resp = await postRequest2({
        path: setUrlParams(URLS.SAVE, "{{article.get_nickname}}"),
        data :
        {
            heading : heading.value,
            subheading : subheading.value,
        }
    })
    if (resp.code === code.OK) 
    {
        sessionStorage.removeItem('heading')
        sessionStorage.removeItem('subheading')
        message("saving")
        return
    }
    error(resp.error);
}

heading.oninput = () => {
    sessionStorage.setItem("heading", heading.value)
}

subheading.oninput = () => {
    sessionStorage.setItem("subheading", subheading.value)
}

heading.onchange = async() => {
    updateArticleHead();
}

subheading.onchange = async() => {
    updateArticleHead();
}

const handleSectionUpdate = () => {
    getElements("section-edit").forEach((section) => {
        let sectionID = section.getAttribute("sectionid")
        let subheading = section.getElementsByClassName("subheading")
        let paragraph = section.getElementsByClassName("paragraph")
        if (subheading.length > 0) {
            subheading[0].oninput = () => {
                sessionStorage.setItem(`${sectionID}-subheading`, subheading[0].value)
            }
        }
        if (paragraph.length > 0) {
            paragraph[0].oninput = () => {
                sessionStorage.setItem(`${sectionID}-paragraph`, paragraph[0].value)
            }
        }
    })
    getElements("section-edit").forEach((section) => {
        section.addEventListener('change', () =>   {
            let sectionID = section.getAttribute("sectionid")
            let subheading = section.getElementsByClassName("subheading")
            subheading = subheading.length>0?subheading[0].value:""
            let paragraph = section.getElementsByClassName("paragraph")
            paragraph = paragraph.length>0?paragraph[0].value:""
            updateSection({sectionID, subheading, paragraph})
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
                        updateSection({sectionID, image:croppedB64})
                    },
                    true
                );
            };
        }
    
        if(section.getAttribute("hasVideo")==="true")
        {
            getElement(`section-video-file-${sectionID}`).onchange = (e) => {
                handleVideoUpload(
                    e,
                    `videoData-${sectionID}`,
                    `videoOutput-${sectionID}`,
                    (B64) => {
                        updateSection({sectionID, video:B64})
                    }
                );
            }
        }
    
        document.querySelectorAll(`#delete-section-${sectionID}`).forEach((delete_button) => {
            delete_button.onclick = async() => {
                const deleted = await handleSectionDeletion(sectionID)
                if (deleted) {
                    getElements("section-content").forEach((content) => {
                        if (content.getAttribute('sectionid') === sectionID)
                            content.outerHTML = ""
                    })
                }
            }
        })
    
    })
}

handleSectionUpdate();


getElement("add-paragraph").onclick = () => {
    console.log("doit")
    if (getElements('temp-paragraphs').length > 0)
        return
    handleSectionCreation();
}

getElement("add-image").onclick = () => {
    handleImageSectionCreation();
}

getElement("add-video").onclick = () => {
    handleVideoSectionCreation();
}

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
    document.querySelectorAll("#publishArticle").forEach((publish_button) => {
        publish_button.onclick = async(_) => {
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
}
{% endif %}

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

const sync = () => {
    Object.keys(sessionStorage).forEach((key) => {
        if (key.includes('-paragraph')) {
            let sectionID = key.replace("-paragraph", '')
            let paragraph = sessionStorage.getItem(key)
            getElement(key).innerHTML = paragraph
            updateSection({sectionID, paragraph})
        }
        else if(key.includes('-subheading')) {
            let sectionID = key.replace("-subheading", '')
            let subheading = sessionStorage.getItem(key)
            getElement(key).defaultValue = subheading
            getElement(key+"-2").defaultValue = subheading
            updateSection({sectionID, subheading})
        }
        else if(key=='heading') {
            getElement('heading').value = sessionStorage.getItem(key)
            updateArticleHead()
        }
        else if(key=='subheading') {
            getElement('subheading').value = sessionStorage.getItem(key)
            updateArticleHead()
        }
    })
}
sync();