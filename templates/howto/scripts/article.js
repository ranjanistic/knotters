self = "{{request.GET.self}}"=="True"?true:false
size = getElement("size").value
for(let i=1; i<=size; i++)
{
    if (self) {
        getElement(`section-file-${i}`).onchange = (e) => {
            handleCropImageUpload(
                e,
                `imageData-${i}`,
                `imageOutput-${i}`,
                (croppedB64) => {
                    hide(getElement(`add-image-view-${i}`))
                    show(getElement(`imageOutput-${i}`))
                }
            );
        };
    }
}

articleID = getElement("articleid").value 
getElement("deleteArticle").onclick = async(_) =>{
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
}
getElement("draftArticle").onclick = async(_) => {
    draft = getElement("draft").value
    if(draft=="True")
        draft = false
    else
        draft = true
    resp = await postRequest2({
        path: setUrlParams(URLS.Howto.DRAFT, articleID),
        data : {
            draft : draft
        },
    })
    if(resp.code === code.OK)
    {
        if (draft)
            relocate({query:{
                s: STRING.article_drafted
            }})
        else
            relocate({query:{
                s: STRING.article_published
            }})
    }
}
