const tabindex = Number("{{request.GET.tab}}") || false;
initializeTabsView({
    onEachTab: async (tab) => {
        return await getRequest(setUrlParams(URLS.LABEL_TYPE, tab.id));
    },
    uniqueID: "labeltab",
    onShowTab: (tab) => {
        getElement(`create-${tab.id}`).onclick = (_) => {
            alertify
                .confirm(
                    `Create new ${tab.id}`,
                    `
                <input id="new-${tab.id}-name" class="wide" placeholder="Name of the ${tab.id}" required type="text" />
            `,
                    async () => {
                        let name = String(
                            getElement(`new-${tab.id}-name`).value
                        ).trim();
                        if (!name)
                            return error(
                                `Name is required for a new ${tab.id}.`
                            );
                        const data = await postRequest(
                            setUrlParams(URLS.LABEL_CREATE, tab.id),
                            { name }
                        );
                        if (!data) return;
                        if (data.code === code.OK) {
                            message(`${name} ${tab.id} was created.`);
                            tab.click();
                            return;
                        }
                        error(data.error);
                    },
                    () => {}
                )
                .set("closable", false)
                .set("labels", { ok: "Create", cancel: "Discard" });
        };
        if (tab.id === "tag") {
            getElements("delete-tag").forEach((tag) => {
                tag.onclick = (e) => {
                    const name = e.target.getAttribute("data-tagname");
                    const tagID = e.target.getAttribute("data-tagID");
                    alertify
                        .confirm(
                            `Delete tag ${name}?`,
                            `
                        <h4>Delete tag '${name}' from ${APPNAME}, are you sure? (This tag will be removed from all linked assets)</h4>
                        `,
                            async () => {
                                const data = await postRequest(
                                    setUrlParams(
                                        URLS.LABEL_DELETE,
                                        tab.id,
                                        tagID
                                    )
                                );
                                if (!data) return;
                                if (data.code === code.OK) {
                                    hideElement(`tag-view-${tagID}`);
                                    message(`Tag '${name}' was deleted.`);
                                    return;
                                }
                                error(data.error);
                            },
                            () => {}
                        )
                        .set("closable", false)
                        .set("labels", { ok: "Delete", cancel: "Cancel" });
                };
            });
        }
    },
    tabindex,
});
