intializeTabsView(async (tabID) => {
    return await getRequest(`/people/profiletab/${userID}/${tabID}`);
}, "profiletab");

intializeTabsView(
    async (tabID) => {
        return await getRequest(`/people/settingtab/${tabID}`);
    },
    "profilestab",
    "set-tab",
    "active",
    "primary",
    "stabview",
    "sloader"
);

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
