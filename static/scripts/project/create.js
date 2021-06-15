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
          alert(res.body.error);
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
    // postRequest("/projects/submit", {
    //   projectname: formValues[0].value,
    //   reponame: formValues[1].value,
    //   projectabout: formValues[2].value,
    //   tags: formValues[3].value,
    //   projectcategory: formValues[4].value,
    //   description: formValues[5].value,
    // }).then((res) => {
    //   if (res.body.code === "OK") {
    //     return window.location.replace(`/projects/profile/${reponame}`);
    //   }
    //   actionLoader(false);
    //   alert(res.body.error);
    // });
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

/** =========== Tags in input field ================ */

const tagbutton = document.querySelectorAll(".tagbutton");
const tagsname = document.querySelectorAll(".tagsname");

const displaytag = (index) => {
  tagbutton[index].style.display = "none";
};

tagsname.forEach((item, index) => {
  item.addEventListener("click", function tagInput() {
    formValues[3].value += item.innerHTML.replace("#", "").trim() + " ,";
    displaytag(index);
  });
});

/* ========== Image-Preview ============= */
//! Image cropper (not working for uploaded images)

var modal = document.getElementById("myModal");
var image = document.getElementById("modal-id");
var imageOutput = document.getElementById("test");

var loadFile = function () {
  const file = document.querySelector("input[type=file]").files[0];
  const reader = new FileReader();

  reader.addEventListener(
    "load",
    function () {
      const base64String = reader.result;
      console.log(base64String);
      image.src = base64String;
    },
    false
  );

  if (file) {
    reader.readAsDataURL(file);
  }

  console.log(image.src);
  console.log(image);

  var span = document.getElementsByClassName("close")[0];

  modal.style.display = "block";

  span.onclick = function () {
    modal.style.display = "none";
  };

  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };
};

/* ============== Cropper ================== */
const cropper = new Cropper(imageOutput, {
  aspectRatio: 4 / 3,
  viewMode: 3,
  responsive: true,

  crop(event) {
    console.log(event.detail.x);
    console.log(event.detail.y);
    console.log(event.detail.width);
    console.log(event.detail.height);
    console.log(event.detail.rotate);
    console.log(event.detail.scaleX);
    console.log(event.detail.scaleY);
  },
});

var saveBtn = document.getElementById("saveBtn");

saveBtn.addEventListener("click", function cropImageFunction() {
  var cropedImage = cropper.getCroppedCanvas().toDataURL("image/png");
  document.getElementById("output").src = cropedImage;
  console.log(cropedImage);
  modal.style.display = "none";
});
