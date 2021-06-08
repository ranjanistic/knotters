/* ======= Create-project-form ========*/

var currentStep = 0;
showStep(currentStep);

function showStep(n) {
  var x = document.getElementsByClassName("step-tab");
  x[n].style.display = "block";
  if (n == 0) {
    document.getElementById("prevBtn").style.display = "none";
  } else {
    document.getElementById("prevBtn").style.display = "inline";
  }

  if (n == x.length - 2) {
    document
      .getElementById("nextBtn")
      .addEventListener("click", function preview() {
        document.getElementById(
          "titlePreview"
        ).innerHTML = document.getElementById("projectname").value;
        document.getElementById(
          "usernamePreview"
        ).innerHTML = document.getElementById("reponame").value;
        document.getElementById(
          "aboutPreview"
        ).innerHTML = document.getElementById("projectabout").value;
        document.getElementById(
          "tagsPreview"
        ).innerHTML = document.getElementById("tags").value;
        document.getElementById(
          "categoryPreview"
        ).innerHTML = document.getElementById("projectcategory").value;
        document.getElementById(
          "descriptionPreview"
        ).innerHTML = document.getElementById("description").value;
      });
  }
  if (n == x.length - 1) {
    document.getElementById("nextBtn").type = "submit";
    document.getElementById("nextBtn").innerHTML = "Create";
  } else {
    document.getElementById("nextBtn").innerHTML =
      "Next<i class='material-icons big-icon'>navigate_next</i>";
  }
  fixStepIndicator(n);
}

function nextPrev(n) {
  var x = document.getElementsByClassName("step-tab");
  if (n == 1 && !validateForm()) return false;
  x[currentStep].style.display = "none";
  currentStep = currentStep + n;
  if (currentStep >= x.length) {
    document.getElementById("create-project-form").submit();
    return false;
  }
  showStep(currentStep);
}

function validateForm() {
  var x,
    y,
    i,
    valid = true;
  x = document.getElementsByClassName("step-tab");
  y = x[currentStep].getElementsByTagName("input");
  for (i = 0; i < y.length; i++) {
    if (y[i].value == "") {
      y[i].className += " invalid";
      valid = false;
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

/* ========== Image-Preview ============= */

var loadFile = function (event) {
  var image = document.getElementById("output");
  image.src = URL.createObjectURL(event.target.files[0]);
};
