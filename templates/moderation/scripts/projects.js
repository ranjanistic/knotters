{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

const modID = "{{moderation.getID}}";
{% if ismoderator %}
getElements("modaction").forEach((action) => {
    const approve = action.id === "approve";
    const modaction = async () => {
        loader(true);
        message(
            '{% trans "Resolving moderation" %}, {% trans "please wait" %}.'
        );
        const data = await postRequest(setUrlParams(URLS.ACTION, modID), {
            approve,
        });
        if (!data) return loader(false);
        if (data.code === code.OK) {
            success("Resolved.");
            window.location.reload();
        } else {
            loader(false);
            error(data.error);
        }
    };
    action.addEventListener("click", () => {
        Swal.fire({
            title: `{% trans "Final confirmation" %}`,
            html: `<h4>Are you sure that to <span class="${
                approve ? "positive" : "negative"
            }-text">${
                action.id
            }</span> this project {{moderation.project.name}} (@{{moderation.project.codename}}) 
            will be your final decision?
                <br/><br/>
            <h5>{% trans "This action is irreversible." %}</h5>`,
            showConfirmButton: approve,
            showDenyButton: !approve,
            denyButtonText: "Reject this project",
            confirmButtonText: "Approve this project",
            cancelButtonText: "No, wait!",
        }).then(async (result) => {
            if (result.isConfirmed || result.isDenied) {
                await modaction();
            }
        });
    });
});
{% endif %}
getElement("report-moderation").onclick = async () => {
    await violationReportDialog(
        URLS.REPORT_MODERATION,
        {
            moderationID: "{{moderation.get_id}}",
        },
        "",
        URLS.REPORT_CATEGORIES
    );
};
