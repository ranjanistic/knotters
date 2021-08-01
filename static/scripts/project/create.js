const actionLoader = (visible = true) => {
    visibleElement("actionloader", visible);
    visibleElement("actionbuttons", !visible);
};
actionLoader();
const stepviews = getElements("step-tab");
const nextStepBtn = getElement("nextBtn");
const prevStepBtn = getElement("prevBtn");

const previews = Array.from(
    document.querySelectorAll(
        "#projectnamepreview, #reponamepreview, #projectaboutpreview, #descriptionpreview, #projectcategorypreview, #tagspreview, #referurlpreview"
    )
);
const formValues = Array.from(
    document.querySelectorAll(
        "#projectname, #reponame, #projectabout, #description, #projectcategory, #tags, #referurl"
    )
);
const validationError = Array.from(
    document.querySelectorAll(
        "#projectnameerror, #reponameerror, #projectabouterror,#descriptionerror, #projectcategoryerror, #tagserror, #referurlerror"
    )
);

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
        setHtmlContent(nextStepBtn, `Submit ${Icon("done", "big-icon")}`);
    } else {
        setHtmlContent(
            nextStepBtn,
            `Next ${Icon("navigate_next", "big-icon")}`
        );
    }
    fixStepIndicator(n);
};

const nextPrev = (n) => {
    if (n == 1 && !validateForm()) return false;
    if (!currentStep) {
        actionLoader();
        postRequest(setUrlParams(URLS.CREATEVALIDATEFIELD, "reponame"), {
            reponame: formValues[1].value,
        })
            .then((res) => {
                actionLoader(false);
                if (res.code === "OK") {
                    hide(stepviews[currentStep]);
                    currentStep = currentStep + n;
                    showStep(currentStep);
                } else {
                    if (!res.error) return error();
                    validationError[1].innerHTML = res.error;
                }
            })
            .catch((error) => {
                alertify.error(error);
            });
    } else {
        if (n > 0 && currentStep === stepviews.length - 1) {
            if (!validateForm())
                return alertify.error(
                    "Some values are invalid. Please refresh page and start over."
                );
            if (!getElement("acceptterms").checked) {
                return alertify.error(
                    "Please check the acceptance of terms checkbox at bottom."
                );
            }

            nextStepBtn.type = "submit";
            actionLoader(true);
            subLoader(true);
            alertify.message("Creating project...");
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

const expr = {
    reg: {
        projectname: /^[a-zA-Z0-9 ]{1,40}$/,
        reponame: /^[a-z\-]{2,15}$/,
        projectabout: /^[a-zA-Z0-9.:,_= \?\/\-]{1,200}$/,
        tags: /^[a-zA-Z_, ]{3,60}/,
        projectcategory: /^[a-zA-Z ]{3,}$/,
        description: /^[a-zA-Z0-9-:,_.= \?\/\-]{5,5000}$/,
        referurl: /^(|https?:\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)$/,
    },
    err: {
        projectname: "Only alphabets & numbers allowed, max 40.",
        reponame:
            "Only lowercase alphabets & single hyphens in middle allowed with min 3 & max 15 characeters.",
        projectabout:
            "Only communicative language characters allowed, max 200.",
        tags:
            "Please type relevent valid keywords separated by comma, max 5 tags.",
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
                if (!expr.reg[el.id].test(el.value)) {
                    el.classList.add("invalid");
                    validationError[e + currentStep * 2].innerHTML =
                        expr.err[el.id];
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

const tagbutton = getElements("tagbutton");

tagbutton.forEach((button) => {
    button.onclick = (e) => {
        if (expr.reg.tags.test(formValues[5].value)) {
            formValues[5].value +=
                button.innerHTML
                    .replace("#", formValues[5].value.endsWith(",") ? "" : ",")
                    .trim() + ", ";
        } else {
            formValues[5].value =
                button.innerHTML.replace("#", "").trim() + ", ";
        }
        formValues[5].value = formValues[5].value.trim();
        validateForm(formValues[5].id);
        hide(button);
    };
});

getElement("projectimage").onchange = (e) => {
    handleCropImageUpload(e, "projectImageData", "projectImageOutput", (_) => {
        getElement("uploadprojectimagelabel").innerHTML = "Selected";
    });
};

formValues.forEach((value) => {
    value.value = localStorage.getItem(`createproject${value.id}`) || "";
    value.onblur = (_) => {
        validateForm(value.id);
    };
});
validationError.forEach((value) => {
    value.classList.add("w3-right", "bold");
});

showStep(currentStep);
actionLoader(false);

getElement("more-licenses").onclick = async _ => {
    const data = await postRequest(URLS.LICENSES)
    if(!data) return
    if(data.code!==code.OK){
        return error(data.error)
    }
    let licenses = '';
    data.licenses.forEach((license)=>{
        licenses+=`<button type="button" class="license-choice" id="${license.id}" title="${license.name}: ${license.description}">${license.name}</button>`
    })
    alertify
        .confirm(
            `<h6>Licenses</h6>`,
            `
        <div class="w3-row">
        <button class="primary" id="custom-license">${Icon('add')} Add custom license</button>
        </div>
        <div class="w3-row">
        ${licenses}
        </div>
        `,
            () => {},
            () => {}
        )
        .set("closable", false)
        .set("labels", {
            ok: "Set license",
            cancel: "Cancel",
        })

    getElement('custom-license').onclick=_=>{
        //customLicenseDialog()
    }
    loadLicenseChoices()
};

const loadLicenseChoices = () => 
    initializeTabsView({
        uniqueID: "license",
        activeTabClass: "positive text-positive",
        inactiveTabClass: "primary dead-text",
        tabsClass: "license-choice",
        onEachTab: (tab) => {
            getElement("license").value = tab.id;
        },
    });

alertify.closeAll();
loadLicenseChoices()