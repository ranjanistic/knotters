const actionLoader = (visible = true) => {
    visibleElement("actionloader", visible);
    visibleElement("actionbuttons", !visible);
};
actionLoader();
const stepviews = getElements("step-tab");
const nextStepBtn = getElement("nextBtn");
const prevStepBtn = getElement("prevBtn");

const previews = document.querySelectorAll(
    "#titlePreview, #usernamePreview, #aboutPreview, #tagsPreview, #categoryPreview, #descriptionPreview"
);
const formValues = document.querySelectorAll(
    "#projectname, #reponame, #projectabout, #tags, #projectcategory, #description"
);
const validationError = document.querySelectorAll(
    "#projectnameerror, #reponameerror, #projectabouterror,#tagserror,#projectcategoryerror,#descriptionerror"
);

let currentStep = 0;

const showStep = (n) => {
	console.log(n,stepviews.length)
    if (n >= stepviews.length) return;
    show(stepviews[n]);
    if (!n) {
        hide(prevStepBtn);
    } else {
        prevStepBtn.style.display = "inline";
    }

    if (n == stepviews.length - 2) {
        nextStepBtn.addEventListener("click", function preview() {
            for (var k = 0; k < previews.length; k++) {
                previews[k].innerHTML = formValues[k].value;
            }
        });
    }
    if (n == stepviews.length - 1) {
        nextStepBtn.type = "submit";
        nextStepBtn.innerHTML =
            "Submit <i class='material-icons big-icon'>done</i>";
    } else {
        nextStepBtn.innerHTML =
            "Next<i class='material-icons big-icon'>navigate_next</i>";
    }
    fixStepIndicator(n);
};

const nextPrev = (n) => {
    if (n == 1 && !validateForm()) return false;
    if (!currentStep) {
        actionLoader();
        postRequest("/projects/create/validate/reponame", {
            reponame: formValues[1].value,
        })
            .then((res) => {
                actionLoader(false);
                console.log(res);
                if (res.code === "OK") {
                    hide(stepviews[currentStep]);
                    currentStep = currentStep + n;
                    showStep(currentStep);
                } else {
                    validationError[1].innerHTML = res.error;
                }
            })
            .catch((error) => {
                alertify.error(error);
            });
    } else {
        if (n > 0 && currentStep >= stepviews.length - 1 ) {
            actionLoader(true);
            if (!validateForm())
                return alertify.error(
                    "Some values are invalid. Please refresh page and start over."
                );
            getElement("create-project-form").submit();
            return false;
        } else {
            hide(stepviews[currentStep]);
			currentStep += n;
            showStep(currentStep);
        }
    }
};

const expr = {
    reg: {
        projectname: /^[a-zA-Z0-9 ]*$/,
        reponame: /^[a-zA-Z-]*$/,
        projectabout: /^[a-zA-Z0-9. ]*$/,
        tags: /^[a-zA-Z_, ]*$/,
        projectcategory: /^[a-zA-Z ]*$/,
        description: /^[a-zA-Z0-9-_. ]*$/,
    },
    err: {
        projectname: "Only letters & numbers allowed.",
        reponame: "Only letters & hyphens in middle allowed.",
        projectabout: "Only letters & numbers allowed.",
        tags: "Please type relevent keywords separated by comma.",
        projectcategory: "Please set an appropriate category for your project.",
        description:
            "Please describe your project properly so that moderators can understand it better.",
    },
};

const validateForm = (id) => {
    let valid = true;

    stepviews.some((step, s) => {
        if (s === currentStep) {
            const validator = (el, e) => {
                el.value = String(el.value).trim();
                if (!el.value) {
                    el.classList.add("invalid");
                    valid = false;
                } else {
                    if (!expr.reg[el.id].test(el.value)) {
                        el.classList.add("invalid");
                        validationError[e + currentStep * 2].innerHTML =
                            expr.err[el.id];
                        valid = false;
                    } else {
                        el.classList.remove("invalid");
                        validationError[e + currentStep * 2].innerHTML = "";
                    }
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
        formValues[3].value += button.innerHTML.replace("#", "").trim() + ", ";
        hide(button);
    };
});

getElement("projectimage").onchange = (e) => {
    handleCropImageUpload(e, "projectImageData", "projectImageOutput", (_) => {
        getElement("uploadprojectimagelabel").innerHTML = "Selected";
    });
};

// window.onbeforeunload = (_) => {
//     return "wait";
// };

formValues.forEach((value) => {
    value.onblur = (_) => {
        validateForm(value.id);
    };
});
validationError.forEach((value) => {
    value.classList.add("w3-right", "bold");
});

showStep(currentStep);
actionLoader(false);
