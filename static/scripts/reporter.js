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
            `${
                isReport ? "Report" : "Feedback"
            } received and will be looked into.`
        );
        return true;
    }
    error(data.error);
    return false;
};

const reportFeedbackView = () => {
    Swal.fire({
        title: "Report or Feedback",
        html: `
        <div class="w3-row w3-center report-feed-view" id="report-view">
            <textarea class="wide" rows="3" id="report-feed-summary" placeholder="Short description" ></textarea><br/><br/>
            <textarea class="wide" rows="5" id="report-feed-detail" placeholder="Explain everything here in detail (optional)" ></textarea>
            <h6>Your identity will remain private.</h6>
            <input class="wide" type="email" autocomplete="email" id="report-feed-email" placeholder="Your email address (optional)" /><br/><br/>
        </div>
        `,
        showDenyButton: true,
        showCancelButton: true,
        showConfirmButton: true,
        confirmButtonText: "Send Feedback",
        denyButtonText: "Send Report",
        cancelButtonText: "Cancel",
        focusConfirm: false,
        preConfirm: () => {
            const summary = String(
                getElement("report-feed-summary").value
            ).trim();
            if (!summary) {
                error("Short description required");
                return false;
            }
            return true;
        },
        preDeny: () => {
            const summary = String(
                getElement("report-feed-summary").value
            ).trim();
            if (!summary) {
                error("Short description required");
                return false;
            }
            return true;
        },
    }).then(async (result) => {
        if (result.isDismissed) return;
        let data = {};
        const summary = String(getElement("report-feed-summary").value).trim();
        if (!summary) {
            error("Short description required");
            return false;
        }
        data["summary"] = summary;
        data["detail"] = String(getElement("report-feed-detail").value).trim();
        data["isReport"] = result.isDenied;
        data["email"] = String(getElement("report-feed-email").value).trim();
        message(`Submitting ${result.isDenied ? "report" : "feedback"}...`);
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
    const data = await getRequest(reportCatURL || URLS.REPORT_CATEGORIES);
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
        title: `Report ${reportTarget}`,
        html: `
        <select class="text-medium wide" id='violation-report-category' required>
                ${options}
            </select>
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: `${Icon("report")} Report ${reportTarget}`,
        cancelButtonText: "No, go back",
        preConfirm: () => {
            return getElement("violation-report-category").value;
        },
    }).then(async (result) => {
        if (result.isConfirmed) {
            loader();
            message("Reporting...");
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
                    `Reported${" " + reportTarget}. We\'ll investigate.`
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
