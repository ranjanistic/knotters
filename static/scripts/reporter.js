const reportFeedback = async ({
    isReport = true,
    email = "",
    category = "",
    summary = "",
    detail = "",
}) => {
    const data = await postRequest(
        isReport
            ? URLS.CREATE_REPORT || URLS.Management.CREATE_REPORT
            : URLS.CREATE_FEED || URLS.Management.CREATE_FEED,
        {
            email,
            category,
            summary,
            detail,
        }
    );
    if (!data) return false;
    if (data.code === code.OK) {
        success(
            `${isReport ? STRING.report : STRING.feedback} ${
                STRING.received_and_noted
            }`
        );
        return true;
    }
    error(data.error);
    return false;
};

const reportFeedbackView = () => {
    Swal.fire({
        title: `${STRING.report} ${STRING.or} ${STRING.feedback}`,
        html: `
        <div class="w3-row w3-center report-feed-view" id="report-view">
            <textarea class="wide" rows="3" id="report-feed-summary" placeholder="${STRING.short_desc}" ></textarea><br/><br/>
            <textarea class="wide" rows="5" id="report-feed-detail" placeholder="${STRING.explain_in_detail} (${STRING.optional})" ></textarea>
            <h6>${STRING.your_id_remain_private}</h6>
            <input class="wide" type="email" autocomplete="email" id="report-feed-email" placeholder="${STRING.your_email_addr} (${STRING.optional})" /><br/><br/>
        </div>
        `,
        showDenyButton: true,
        showCancelButton: true,
        showConfirmButton: true,
        confirmButtonText: `${STRING.send} ${STRING.feedback}`,
        denyButtonText: `${STRING.send} ${STRING.report}`,
        cancelButtonText: STRING.cancel,
        focusConfirm: false,
        preConfirm: () => {
            const summary = String(
                getElement("report-feed-summary").value
            ).trim();
            if (!summary) {
                error(STRING.short_desc_required);
                return false;
            }
            return true;
        },
        preDeny: () => {
            const summary = String(
                getElement("report-feed-summary").value
            ).trim();
            if (!summary) {
                error(STRING.short_desc_required);
                return false;
            }
            return true;
        },
    }).then(async (result) => {
        if (result.isDismissed) return;
        let data = {};
        const summary = String(getElement("report-feed-summary").value).trim();
        if (!summary) {
            error(STRING.short_desc_required);
            return false;
        }
        data["summary"] = summary;
        data["detail"] = String(getElement("report-feed-detail").value).trim();
        data["isReport"] = result.isDenied;
        data["email"] = String(getElement("report-feed-email").value).trim();
        message(
            `${STRING.submitting} ${
                result.isDenied ? STRING.report : STRING.feedback
            }...`
        );
        loader();
        await reportFeedback(data);
        loader(false);
    });
};

const violationReportDialog = async (
    reportURL = "",
    reportTargetData = {},
    reportTarget = "",
    reportCatURL = ""
) => {
    const data = await getRequest2({ path:reportCatURL || URLS.REPORT_CATEGORIES, allowCache:true, retainCache: true });
    if (!data) return false;
    if (data.code !== code.OK) {
        error(data.error);
        return false;
    }
    let options = "";
    data.reports.forEach((rep) => {
        options += `<option class="text-medium" value='${rep.id}'>${rep.name}</option>`;
    });
    await Swal.fire({
        title: `${STRING.report} ${reportTarget}`,
        html: `
            ${STRING.select_category}<br/><br/>
        <select class="text-medium wide negative-text pallete-slab" id='violation-report-category' required>
                ${options}
            </select>
        `,
        focusConfirm: false,
        showConfirmButton: false,
        showDenyButton: true,
        showCancelButton: true,
        denyButtonText: `${Icon("report")} ${STRING.report} ${reportTarget}`,
        cancelButtonText: STRING.no_wait,
        preDeny: () => {
            return getElement("violation-report-category").value;
        },
    }).then(async (result) => {
        if (result.isDenied) {
            loader();
            message(STRING.reporting);
            const data = await postRequest2({
                path: reportURL,
                data: {
                    report: result.value,
                    ...reportTargetData,
                },
                retainCache: true,
            });
            loader(false);
            if (!data) return;
            if (data.code === code.OK) {
                return message(
                    `${STRING.reported}${" " + reportTarget}. ${
                        STRING.we_will_investigate
                    }`
                );
            }
            error(data.error);
        }
    });
};

const loadReporters = () => {
    getElements("report-button").forEach((report) => {
        report.type = "button";
        report.addEventListener("click", () => {
            reportFeedbackView();
        });
    });
};
