{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

getElement("browse-search-clear").onclick = () => {
    getElements("search-view").forEach((x)=>{
        x.innerHTML = ''
    });
    hideElement("browse-search-actions");
};
getElement("browse-search-input").oninput = (e) => {
    visibleElement("browse-search-actions", String(e.target.value).trim());
};
getElement("browse-search-exec").onclick = async () => {
    let query = String(getElement("browse-search-input").value).trim();
    if (!query)
        return message('{% trans "Type something to search anything" %}');
    const data = await getRequest2({
        path: URLS.SEARCH_RESULT,
        data: { query },
    });
    if (!data) return;
    if (data.code!=CODE.OK) return error(data.error);
    setHtmlContent(getElement("projects"), data.projects, loadBrowserSwiper)
    setHtmlContent(getElement("people"), data.people, loadBrowserSwiper)
    setHtmlContent(getElement("compete"), data.compete, loadBrowserSwiper)
    setHtmlContent(getElement("snapshot"), data.snapshot, loadBrowserSwiper)
};
getElement("search-projects-form").onsubmit = (e) => {
    getElement("browse-search-exec").click();
};
if ("{{request.GET.query}}") {
    window.location.href = "#mainframe";
    getElement("browse-search-input").value = "{{request.GET.query}}";
    showElement("browse-search-actions");
    getElement("browse-search-exec").click();
}
