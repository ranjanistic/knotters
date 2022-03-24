const loadDynamicContent = async () => {
    getElements("dynamic-content-view").forEach(async (element) => {
        // const callingMethod = () => {
        //     let url = element.getAttribute("data-contentpath");
        //     const method = element.getAttribute("data-pathmethod");
        //     let data = element.getAttribute("data-pathmethod");
        //     let requestor = getRequest2;
        //     if (method.toUpperCase() == "POST") {
        //         requestor = postRequest2;
        //     }
        //     try{
        //         data = JSON.parse(data);
        //     }catch{}

        //     const done = await requestor({
        //         path: url,
        //     });
        //     if (method == "POST") {
        //         if (done.code == CODE.OK) {
        //             setHtmlContent(element, done.html);
        //         } else {
        //             setHtmlContent(element, loadErrorHTML(`${url}retry`));
        //             getElement(`${url}retry`).onclick = (_) => callingMethod();
        //             setHtmlContent(element, errorHTML);
        //         }
        //     } else {

        //     }
        // };
        // callingMethod()
    });
};
