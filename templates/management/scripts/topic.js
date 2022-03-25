{% if topic.isDeletable %}
const name = "{{topic.name}}",
    topicID = "{{topic.get_id}}";
getElement("delete-topic-{{topic.get_id}}").onclick = (_) => {
    alertify
        .confirm(
            `Delete topic ${name}?`,
            `
        <h4>Delete topic '${name}' from ${APPNAME}, are you sure? (This topic will be removed from all linked assets)</h4>
        `,
            async () => {
                const data = await postRequest(
                    setUrlParams(
                        URLS.LABEL_DELETE,
                        "{{topic.label_type}}",
                        topicID
                    )
                );
                if (!data) return;
                if (data.code === code.OK) {
                    futuremessage(`Topic '${name}' was deleted.`);
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
