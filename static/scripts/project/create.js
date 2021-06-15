/* ======= Create-project-form ========*/

const actionLoader = (visible = true) => {
  visible ? show(getElement("actionloader")) : hide(getElement("actionloader"));
  visible
    ? hide(getElement("actionbuttons"))
    : show(getElement("actionbuttons"));
};

actionLoader(false);

var nextStepBtn = document.getElementById("nextBtn");
var prevStepBtn = document.getElementById("prevBtn");
var previews = document.querySelectorAll(
  "#titlePreview, #usernamePreview, #aboutPreview, #tagsPreview, #categoryPreview, #descriptionPreview"
);
var formValues = document.querySelectorAll(
  "#projectname, #reponame, #projectabout, #tags, #projectcategory, #description"
);
var validationError = document.querySelectorAll(
  "#projectnameerror, #reponameerror, #projectabouterror,#tagserror,#projectcategoryerror,#descriptionerror "
);
var currentStep = 0;
showStep(currentStep);

function showStep(n) {
  var x = document.getElementsByClassName("step-tab");
  x[n].style.display = "block";
  if (n == 0) {
    prevStepBtn.style.display = "none";
    nextStepBtn.addEventListener("click", function () {
      postRequest("https://jsonplaceholder.typicode.com/posts", {
        reponame: formValues[1].value,
      })
        .then((res) => {
          if (res.body.code === "OK") {
            console.log(res);
          }
        })
        .catch((error) => {
          console.log(error);
        });
    });
  } else {
    prevStepBtn.style.display = "inline";
  }

  if (n == x.length - 2) {
    nextStepBtn.addEventListener("click", function preview() {
      for (var k = 0; k < previews.length; k++) {
        previews[k].innerHTML = formValues[k].value;
      }
    });
  }
  if (n == x.length - 1) {
    nextStepBtn.type = "submit";
    nextStepBtn.innerHTML = "Create";
  } else {
    nextStepBtn.innerHTML =
      "Next<i class='material-icons big-icon'>navigate_next</i>";
  }
  fixStepIndicator(n);
}

const nextPrev = (n) => {
  var x = document.getElementsByClassName("step-tab");
  if (n == 1 && !validateForm()) return false;
  x[currentStep].style.display = "none";
  currentStep = currentStep + n;
  if (currentStep >= x.length) {
    actionLoader(true);
    document.getElementById("create-project-form").submit();
    return false;
  }
  showStep(currentStep);
};

function validateForm() {
  var x,
    y,
    i,
    valid = true;
  x = document.getElementsByClassName("step-tab");
  y = x[currentStep].getElementsByClassName("big-input");

  var expr = /^[a-zA-Z0-9.-_]*$/;

  for (i = 0; i < y.length; i++) {
    if (y[i].value == "") {
      y[i].className += " invalid";
      valid = false;
    } else {
      if (!expr.test(y[i].value)) {
        y[i].className += " invalid";
        validationError[i].innerHTML =
          "Only Alphabets, Numbers, Dot, hyphen, and underscore allowed";
        valid = false;
      }
    }
  }
  if (valid) {
    document.getElementsByClassName("step")[currentStep].className += " finish";
  }
  return valid;
}

function fixStepIndicator(n) {
  var i,
    x = document.getElementsByClassName("step");
  for (i = 0; i < x.length; i++) {
    x[i].className = x[i].className.replace(" active", "");
  }
  x[n].className += " active";
}


const tagbutton = getElements("tagbutton");


tagbutton.forEach((button, index) => {
  button.onclick= (e)=> {
    formValues[3].value += button.innerHTML.replace("#", "").trim() + ", ";
    hide(tagbutton[index])
  };
});

getElement("projectimage").onchange = (e) => {
  handleCropImageUpload(
      e,
      "projectImageData",
      "projectImageOutput",
      (croppedB64) => {
          getElement("uploadprojectimagelabel").innerHTML = "Selected";
      }
  );
};
