{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

getElement("browse-search-clear").onclick = () => {
    getElement("browse-search-view").innerHTML = "";
    hideElement("browse-search-actions");
};
getElement("browse-search-input").oninput = (e) => {
    visibleElement("browse-search-actions", String(e.target.value).trim());
};
getElement("browse-search-exec").onclick = async () => {
    let query = String(getElement("browse-search-input").value).trim();
    if (!query)
        return message('{% trans "Type something to search licenses" %}');
    const data = await getRequest2({
        path: URLS.LICENSE_SEARCH,
        data: { query },
    });
    if (!data) return;
    setHtmlContent(getElement("browse-search-view"), data, loadBrowserSwiper);
};
getElement("search-license-form").onsubmit = (e) => {
    getElement("browse-search-exec").click();
};
if ("{{request.GET.search}}") {
    getElement("browse-search-input").value = "{{request.GET.search}}";
    showElement("browse-search-actions");
    getElement("browse-search-exec").click();
}
