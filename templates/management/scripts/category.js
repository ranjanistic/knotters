{% if category.isDeletable %}
const catname = "{{category.catname}}",
    categoryID = "{{category.get_id}}";
getElement("delete-category-{{category.get_id}}").onclick = (_) => {
    alertify
        .confirm(
            `Delete category ${catname}?`,
            `
        <h4>Delete category '${catname}' from ${APPNAME}, are you sure? (This category will be removed from all linked assets)</h4>
        `,
            async () => {
                const data = await postRequest(
                    setUrlParams(
                        URLS.LABEL_DELETE,
                        "{{category.label_type}}",
                        categoryID
                    )
                );
                if (!data) return;
                if (data.code === code.OK) {
                    futuremessage(`Category '${catname}' was deleted.`);
                    return window.location.replace("{{URLS.LABELS}}");
                }
                error(data.error);
            },
            () => {}
        )
        .set("closable", false)
        .set("labels", { ok: "Delete", cancel: "Cancel" });
};
{% endif %}
