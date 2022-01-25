const loadBrowserSwiper = () => {
    const x = () => {
        loadCarousels({
            container: "swiper-browser",
            breakpoints: {
                1024: {
                    slidesPerView: 4,
                    spaceBetween: 15,
                },
                768: {
                    slidesPerView: 4,
                    spaceBetween: 10,
                },
                920: {
                    slidesPerView: 4,
                    spaceBetween: 10,
                },
                640: {
                    slidesPerView: 4,
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
    Promise.all(
        getElements("browser-view").map(async (view) => {
            let method = async () => {
                setHtmlContent(view, loaderHTML(`${view.id}-loader`));
                const data = await getRequest2({
                    path: setUrlParams(URLS.BROWSER, view.getAttribute("data-type")),
                    silent: true
                });
                if (!data) {
                    setHtmlContent(
                        view,
                        loadErrorHTML(`${view.id}-load-retry`)
                    );
                    getElement(`${view.id}-load-retry`).onclick = (_) =>
                        method();
                    return;
                }
                setHtmlContent(view, data===true?'':data, loadBrowserSwiper);
                loadBrowserSwiper();
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
