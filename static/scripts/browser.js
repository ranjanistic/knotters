const loadBrowserSwiper = (_) => {
    loadCarousels({
        container: "swiper-browser",
        breakpoints: {
            1024: {
                slidesPerView: 4,
                spaceBetween: 5,
            },
            768: {
                slidesPerView: 3,
                spaceBetween: 5,
            },
            920: {
                slidesPerView: 4,
                spaceBetween: 12,
            },
            640: {
                slidesPerView: 4,
                spaceBetween: 12,
            },
        },
    });
};
const loadNewbieProjects = async () => {
    try {
        const nbview = getElement("newbie-projects-view");
        setHtmlContent(nbview, loaderHTML());
        const data = await getRequest(URLS.Projects.NEWBIES);
        if (!data) {
            setHtmlContent(nbview, loadErrorHTML(`newbie-projects-retry`));
            getElement(`newbie-projects-retry`).onclick = (_) =>
                loadNewbieProjects();
            return;
        }
        setHtmlContent(nbview, data, loadBrowserSwiper);
    } catch {}
};
const loadNewbieProfiles = async () => {
    try {
        const nbprofview = getElement("newbie-profiles-view");
        setHtmlContent(nbprofview, loaderHTML());
        const data = await getRequest(URLS.People.NEWBIES);
        if (!data) {
            setHtmlContent(nbprofview, loadErrorHTML(`newbie-profiles-retry`));
            getElement(`newbie-profiles-retry`).onclick = (_) =>
                loadNewbieProfiles();
            return;
        }
        setHtmlContent(nbprofview, data, loadBrowserSwiper);
    } catch {}
};
