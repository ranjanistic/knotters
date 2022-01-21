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
        const data = await postRequest(
            setUrlParams(URLS.CREATEVALIDATEFIELD, "reponame"),
            {
                reponame:
                    formValues[
                        formValues.indexOf(
                            formValues.find((input) => input.id === "reponame")
                        )
                    ].value,
            }
        );
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
        reponame: /^[a-z\-]{2,15}$/,
        projectabout: /^[a-zA-Z0-9-:,\;\"\&\(\)\!\+\=\]\[\'_.= \?\/\-]{1,200}$/,
        projectcategory: /^[a-zA-Z ]{3,}$/,
        description: /^[a-zA-Z0-9-:,\;\"\&\(\)\!\+\=\]\[\'_.= \?\/\-]{5,5000}$/,
        referurl:
            /^(|https?:\/\/[\w\-_]+(\.[\w\-_]+)+([\w\-\.,@?^=%&amp;:/~\+#]*[\w\-\@?^=%&amp;/~\+#])?)$/,
    },
    err: {
        projectname: "Only alphabets & numbers allowed, max 40.",
        reponame:
            "Only lowercase alphabets & single hyphens in middle allowed with min 3 & max 15 characeters.",
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

getElement("more-licenses").onclick = async (_) => {
    const data = await postRequest(URLS.LICENSES, {
        givenlicenses: getElements("license-choice").map((elem) => elem.id),
    });
    if (!data) return;
    if (data.code !== code.OK) {
        return error(data.error);
    }
    let licenses = [];
    data.licenses.forEach((license) => {
        licenses.push(
            `<button type="button" class="license-choice" id="${license.id.replaceAll(
                "-",
                ""
            )}" title="${license.name}: ${license.description}">${
                license.name
            }</button>`
        );
    });
    Swal.fire({
        title: "Licenses",
        html: `
            <div class="w3-row" id="more-licenses-view">
            ${licenses.join("")}
            </div>
        `,
        showDenyButton: true,
        confirmButtonText: "Set license",
        didOpen: () => {
            loadLicenseChoices();
        },
        preConfirm: () => {
            return getElement("license").value;
        },
    }).then(async (res) => {
        if (res.isConfirmed) {
            let button = licenses.find((lic) => lic.includes(res.value));
            if (!button) return;
            getElement("licenses").innerHTML += button;
            loadLicenseChoices();
        }
    });
};

// const customLicenseDialog = () => {
//     Swal.fire({
//         title: STRING.add_cust_lic,
//         html: `
//         <div class="w3-row">
//         <input class="wide" placeholder="License name" id='custom-license-name' type='text' required maxlength='50'/><br/><br/>
//         <input class="wide" placeholder="Short description" id='custom-license-description' type='text' required maxlength='500'/><br/><br/>
//         <textarea class="wide" placeholder="Full license text" id='custom-license-content' rows="5" type='text' required maxlength='300000'></textarea><br/>
//         <label for='custom-license-public'>
//             <input id='custom-license-public' type='checkbox' />
//             This license can be used without modification by anyone
//         </label>
//         </div>
//         `,
//         showCancelButton: true,
//         showConfirmButton: true,
//         confirmButtonText: STRING.create_lic,
//         cancelButtonText: STRING.cancel,
//         focusConfirm: false,
//         preConfirm: () => {
//             let name = String(getElement("custom-license-name").value).trim();
//             if (!name) {
//                 error(STRING.lic_name_required);
//                 return false;
//             }
//             let description = String(
//                 getElement("custom-license-description").value
//             ).trim();
//             if (!description) {
//                 error(STRING.lic_desc_required);
//                 return false;
//             }
//             let content = String(
//                 getElement("custom-license-content").value
//             ).trim();
//             if (!content) {
//                 error(STRING.lic_text_required);
//                 return false;
//             }
//             return {
//                 name,
//                 description,
//                 content,
//                 public: getElement("custom-license-public").checked,
//             };
//         },
//     }).then(async (result) => {
//         if (result.isConfirmed && result.value) {
//             const data = await postRequest(URLS.ADDLICENSE, {
//                 ...result.value,
//             });
//             if (!data) return;
//             if (data.code === code.OK) {
//                 success(`${data.license.name} ${STRING.lic_created}`);
//                 const button = document.createElement("button");
//                 button.setAttribute("id", data.license.id);
//                 button.setAttribute("title", data.license.description);
//                 button.setAttribute("type", "button");
//                 button.classList.add("license-choice");
//                 getElement("licenses").appendChild(button);
//                 getElement(data.license.id).innerHTML = data.license.name;
//                 loadLicenseChoices();
//             } else {
//                 error(data.error);
//             }
//         }
//     });
// };

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
