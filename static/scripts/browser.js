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
    let browseList = randomizeArray(Object.values(BROWSE));
    let browseIndex = -1;
    Promise.all(
        getElements("browser-view").map(async (view) => {
            browseList = browseList.filter((t) => t!=view.getAttribute('data-type'))
            browseIndex++;
            let method = async () => {
                setHtmlContent(view, loaderHTML(`${view.id}-loader`));
                const data = await getRequest2({
                    path: setUrlParams(URLS.BROWSER, view.getAttribute('data-type')||browseList[browseIndex]),
                    silent: true
                });
                if(browseIndex >= browseList.length){
                    browseList = randomizeArray(Object.values(browseList));
                    browseIndex = 0;
                };
                if (!data) {
                    setHtmlContent(
                        view,
                        loadErrorHTML(`${view.id}-load-retry`)
                    );
                    getElement(`${view.id}-load-retry`).onclick = (_) =>
                        method();
                    return;
                }
                let nildata = data===true||data.code;
                if(nildata){
                    browseIndex--;
                }
                setHtmlContent(view, nildata?'':data, loadBrowserSwiper);
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
