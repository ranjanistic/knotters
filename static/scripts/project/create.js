const previews = Array.from(
    document.querySelectorAll(
        "#projectnamepreview, #reponamepreview, #projectaboutpreview, #descriptionpreview, #projectcategorypreview, #referurlpreview"
    )
);
const formValues = Array.from(
    document.querySelectorAll(
        "#projectname, #reponame, #projectabout, #description, #projectcategory, #referurl"
    )
);
const validationError = Array.from(
    document.querySelectorAll(
        "#projectnameerror, #reponameerror, #projectabouterror,#descriptionerror, #projectcategoryerror, #referurlerror"
    )
);

const actionLoader = (visible = true) => {
    formValues.forEach((input) => {
        input.disabled = visible;
    });
    visibleElement("actionloader", visible);
    visibleElement("actionbuttons", !visible);
};
actionLoader();
const stepviews = getElements("step-tab");
const nextStepBtn = getElement("nextBtn");
const prevStepBtn = getElement("prevBtn");

const showStep = (n) => {
    if (n >= stepviews.length) return;
    show(stepviews[n]);
    if (!n) {
        hide(prevStepBtn);
    } else {
        prevStepBtn.style.display = "inline";
    }

    if (n == stepviews.length - 2) {
        nextStepBtn.addEventListener("click", () => {
            formValues.forEach((input) => {
                previews.some((preview) => {
                    if (`${input.id}preview` === preview.id) {
                        localStorage.setItem(
                            `createproject${input.id}`,
                            input.value
                        );
                        preview.innerHTML = input.value;
                        if (preview.id === "referurlpreview" && input.value) {
                            preview.onclick = (_) => {
                                miniWindow(input.value);
                            };
                        }
                        return true;
                    }
                });
            });
        });
    }
    if (n == stepviews.length - 1) {
        setHtmlContent(
            nextStepBtn,
            `${STRING.submit} ${Icon("done", "big-icon")}`
        );
    } else {
        setHtmlContent(
            nextStepBtn,
            `${STRING.next} ${Icon("navigate_next", "big-icon")}`
        );
    }
    fixStepIndicator(n);
};

const nextPrev = async (n) => {
    if (n == 1 && !validateForm()) return false;
    if (!currentStep) {
        actionLoader();
        let nickname = formValues[formValues.indexOf(formValues.find((input) => input.id === "reponame"))].value
        nickname = nickname.replace(/[^a-z0-9\-]/g, "-").split('-').filter((k)=>k.length).join('-');
        if (!nickname) return;
        formValues[formValues.indexOf(formValues.find((input) => input.id === "reponame"))].value = nickname;
        const data = await postRequest2({
            path: setUrlParams(URLS.CREATEVALIDATEFIELD, "reponame"),
            data: {
                reponame:nickname
            },
            retainCache: true
        });
        actionLoader(false);
        if (!data) return;
        if (data.code === code.OK) {
            hide(stepviews[currentStep]);
            currentStep = currentStep + n;
            showStep(currentStep);
        } else {
            validationError[
                validationError.indexOf(
                    validationError.find(
                        (input) => input.id === "reponameerror"
                    )
                )
            ].innerHTML = data.error;
        }
    } else {
        if (n > 0 && currentStep === stepviews.length - 1) {
            if (!validateForm())
                return error(
                    `${STRING.some_val_invalid} ${STRING.refresh_n_startover}`
                );
            if (
                !getElements("license-choice").some((choice) =>
                    Array.from(choice.classList).includes("positive")
                )
            ) {
                return error(STRING.click_bubble_choose_lic);
            }
            if (!getElement("acceptterms").checked) {
                return error(STRING.pl_accept_terms);
            }
            actionLoader(true);
            subLoader(true);
            formValues.forEach((input) => {
                input.disabled = false;
            });
            message(STRING.creating_project);
            getElement("create-project-form").submit();
            return false;
        } else {
            nextStepBtn.type = "button";
            hide(stepviews[currentStep]);
            currentStep += n;
            showStep(currentStep);
        }
    }
};

const __validator_str_regex = {
    reg: {
        projectname: /^[a-zA-Z0-9 ]{1,40}$/,
        reponame: /^[a-z\-]{2,20}$/,
        projectabout: /^[a-zA-Z0-9-:,\;\"\&\(\)\!\+\=\]\[\'_.= \?\/\-]{1,200}$/,
        projectcategory: /^[a-zA-Z ]{3,}$/,
        description: /^[a-zA-Z0-9-:,\;\"\&\(\)\!\+\=\]\[\'_.= \?\/\-]{5,5000}$/,
        referurl:
            /^(|https?:\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)$/,
    },
    err: {
        projectname: "Only alphabets & numbers allowed, max 40.",
        reponame:
            "Only lowercase alphabets & single hyphens in middle allowed with min 3 & max 15 characters.",
        projectabout:
            "Only communicative language characters allowed, max 200.",
        projectcategory: "Please set an appropriate category for your project.",
        description:
            "Please describe your project in detail, so that moderators can understand it better.",
        referurl: "Provide a valid relevent URL, or leave it empty.",
    },
};

const validateForm = (id) => {
    let valid = true;

    stepviews.some((step, s) => {
        if (s === currentStep) {
            const validator = (el, e) => {
                el.value = String(el.value).trim();
                if (!__validator_str_regex.reg[el.id].test(el.value)) {
                    el.classList.add("invalid");
                    validationError[e + currentStep * 2].innerHTML =
                        __validator_str_regex.err[el.id];
                    valid = false;
                } else {
                    el.classList.remove("invalid");
                    validationError[e + currentStep * 2].innerHTML = "";
                }
            };
            if (id) {
                Array.from(step.getElementsByClassName("big-input")).some(
                    (el, e) => {
                        if (el.id === id) {
                            validator(el, e);
                            return true;
                        }
                    }
                );
            } else {
                Array.from(step.getElementsByClassName("big-input")).forEach(
                    validator
                );
            }
            return true;
        }
    });

    if (valid) {
        getElements("step")[currentStep].classList.add("finish");
    }
    return valid;
};

function fixStepIndicator(n) {
    getElements("step").forEach((step, s) => {
        s === n
            ? step.classList.add("active")
            : step.classList.remove("active");
    });
}

getElement("projectimage").onchange = (e) => {
    handleCropImageUpload(e, "projectImageData", "projectImageOutput", (_) => {
        getElement("uploadprojectimagelabel").innerHTML = "Selected";
    });
};

formValues.forEach((value) => {
    value.value = localStorage.getItem(`createproject${value.id}`) || "";
    value.onblur = (_) => {
        if (validateForm(value.id)) {
            localStorage.setItem(`createproject${value.id}`, value.value);
        }
    };
});

validationError.forEach((value) => {
    value.classList.add("w3-right", "bold");
});

showStep(currentStep);
actionLoader(false);

const loadLicenseChoices = (selected = 0) =>
    initializeTabsView({
        uniqueID: "license",
        activeTabClass: "positive text-positive",
        inactiveTabClass: "primary dead-text",
        tabsClass: "license-choice",
        onEachTab: (tab) => {
            getElement("license").value = tab.id;
        },
        selected,
    });

loadLicenseChoices();
