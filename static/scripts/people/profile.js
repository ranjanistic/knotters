const tabs = getElements("nav-tab"),
    tabview = getElement("tabview");

const showTabLoading = () => {
    tabview.innerHTML = `<div class="loader" id="loader"></div>`;
    openSpinner();
};
const showTabError = () => {
    tabview.innerHTML = "Error";
};

const showTabContent = (content) => {
    tabview.innerHTML = content;
};

tabs.forEach(async (tab, t) => {
    tab.onclick = async () => {
        showTabLoading();
        tabs.forEach((tab1, t1) => {
            if (t1 === t) {
                tab1.classList.add("positive");
                tab1.classList.remove("primary");
            } else {
                tab1.classList.remove("positive");
                tab1.classList.add("primary");
            }
        });
        const response = await getRequest(
            `/people/profiletab/${userID}/${tab.id}`
        );
        hideSpinner();
        return response ? showTabContent(response) : showTabError();
    };
});

tabs[0].click();

if (selfProfile) {
    loadGlobalEditors();
}

//! Image cropper (not working for uploaded images)

var modal = document.getElementById("myModal");
const image = document.getElementById("modal-id");
var imageOutput = document.getElementById("test");

const loadProfile = function (event){
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
}


/* ============== Cropper ================== */

var cropImage = new Cropper(imageOutput, {
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
  var cropedImage = cropImage.getCroppedCanvas().toDataURL("image/png");
  document.getElementById("profilePicOutput").src = cropedImage;
  console.log(cropedImage);
  modal.style.display = "none";
});
