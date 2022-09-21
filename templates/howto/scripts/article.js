const self = "{{ self }}"==='True'
const isRater = "{{isRater}}"==='True'
const articleID = "{{ article.id }}"

{% if sections or self %}
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
    
if (self) {
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