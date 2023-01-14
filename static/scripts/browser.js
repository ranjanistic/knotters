const loadBrowserSwiper = () => {
    const x = () => {
        loadCarousels({
            container: "swiper-browser",
            breakpoints: {
                1024: {
                    slidesPerView: 5,
                    spaceBetween: 15,
                },
                768: {
                    slidesPerView: 5,
                    spaceBetween: 10,
                },
                920: {
                    slidesPerView: 5,
                    spaceBetween: 10,
                },
                640: {
                    slidesPerView: 5,
                    spaceBetween: 10,
                },
            },
        });
        loadCarousels({
            container: "swiper-browser-wide",
            breakpoints: {
                1024: {
                    slidesPerView: 2,
                    spaceBetween: 50,
                },
                768: {
                    slidesPerView: 2,
                    spaceBetween: 10,
                },
                920: {
                    slidesPerView: 2,
                    spaceBetween: 10,
                },
                640: {
                    slidesPerView: 2,
                    spaceBetween: 10,
                },
            },
        });
    };
    x();
    setTimeout(x, 800);
};

const loadBrowsers = () => {
    let browseList = randomizeArray(Object.values(BROWSE));
    let browseIndex = -1;
    Promise.all(
        getElements("browser-view").map(async (view) => {
            browseList = browseList.filter(
                (t) =>
                    t != view.getAttribute("data-type") &&
                    t != BROWSE.PROJECT_SNAPSHOTS
            );
            browseIndex++;
            let method = async () => {
                let browsekey =
                    view.getAttribute("data-type") || browseList[browseIndex];
                if (!browsekey) return;
                setHtmlContent(view, loaderHTML(`${view.id}-loader`));
                const data = await getRequest2({
                    path: setUrlParams(URLS.BROWSER, browsekey),
                    silent: true,
                });
                if (browseIndex >= browseList.length) {
                    browseList = randomizeArray(Object.values(browseList));
                    browseIndex = 0;
                }
                if (!data) {
                    setHtmlContent(
                        view,
                        loadErrorHTML(`${view.id}-load-retry`)
                    );
                    getElement(`${view.id}-load-retry`).onclick = (_) =>
                        method();
                    return;
                }
                let nildata = data === true || data.code;
                if (nildata) {
                    browseIndex--;
                }
                setHtmlContent(view, nildata ? "" : data, loadBrowserSwiper);
                loadBrowserSwiper();
                getElements("browse-admire-project-action").forEach((act) => {
                    act.onclick = async (_) => {
                        if (!AUTHENTICATED) {
                            return refer({
                                path: URLS.Auth.LOGIN,
                                query: {
                                    next: window.location.pathname,
                                },
                            });
                        }
                        const pid = act.getAttribute("data-projectID");
                        const admire = act.getAttribute("data-admires") == "0";
                        const data = await postRequest2({
                            path: setUrlParams(
                                URLS.Projects.TOGGLE_ADMIRATION,
                                pid
                            ),
                            data: {
                                admire,
                            },
                            retainCache: true,
                        });
                        if (data.code !== code.OK) {
                            return error(data.error);
                        }
                        act.setAttribute("data-admires", admire ? 1 : 0);
                        act.classList[admire ? "add" : "remove"]("positive");
                        act.classList[admire ? "remove" : "add"]("primary");
                    };
                });
                getElements("browse-admire-profile-action").forEach((act) => {
                    act.onclick = async (_) => {
                        if (!AUTHENTICATED) {
                            return refer({
                                path: URLS.Auth.LOGIN,
                                query: {
                                    next: window.location.pathname,
                                },
                            });
                        }
                        const uid = act.getAttribute("data-userID");
                        const admire = act.getAttribute("data-admires") == "0";
                        const data = await postRequest2({
                            path: setUrlParams(
                                URLS.People.TOGGLE_ADMIRATION,
                                uid
                            ),
                            data: {
                                admire,
                            },
                            retainCache: true,
                        });
                        if (data.code !== code.OK) {
                            return error(data.error);
                        }
                        act.setAttribute("data-admires", admire ? 1 : 0);
                        act.classList[admire ? "add" : "remove"]("positive");
                        act.classList[admire ? "remove" : "add"]("primary");
                    };
                });
                getElements("browse-admire-article-action").forEach((act) => {
                    act.onclick = async (_) => {
                        if (!AUTHENTICATED) {
                            return refer({
                                path: URLS.Auth.LOGIN,
                                query: {
                                    next: window.location.pathname,
                                },
                            });
                        }
                        const aid = act.getAttribute("data-articleID");
                        const admire = act.getAttribute("data-admires") == "0";
                        const data = await postRequest2({
                            path: setUrlParams(
                                URLS.Howto.TOGGLE_ADMIRATION,
                                aid
                            ),
                            data: {
                                admire,
                            },
                            retainCache: true,
                        });
                        if (data.code !== code.OK) {
                            return error(data.error);
                        }
                        act.setAttribute("data-admires", admire ? 1 : 0);
                        act.classList[admire ? "add" : "remove"]("positive");
                        act.classList[admire ? "remove" : "add"]("primary");
                    };
                });
                getElements("browse-admire-compete-action").forEach((act) => {
                    act.onclick = async (_) => {
                        if (!AUTHENTICATED) {
                            return refer({
                                path: URLS.Auth.LOGIN,
                                query: {
                                    next: window.location.pathname,
                                },
                            });
                        }
                        const cid = act.getAttribute("data-compID");
                        const admire = act.getAttribute("data-admires") == "0";
                        const data = await postRequest2({
                            path: setUrlParams(
                                URLS.Compete.TOGGLE_ADMIRATION,
                                cid
                            ),
                            data: {
                                admire,
                            },
                            retainCache: true,
                        });
                        if (data.code !== code.OK) {
                            return error(data.error);
                        }
                        act.setAttribute("data-admires", admire ? 1 : 0);
                        act.classList[admire ? "add" : "remove"]("positive");
                        act.classList[admire ? "remove" : "add"]("primary");
                    };
                });
            };
            return await method();
        })
    )
        .then(() => {
            loadBrowserSwiper();
        })
        .catch((e) => {
            console.warn(e);
        });
};
