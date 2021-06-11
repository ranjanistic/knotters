async function openTab(tabName) {
  // await getApi(tabName);
  var i;
  var x = document.getElementsByClassName("tab");
  for (i = 0; i < x.length; i++) {
    x[i].style.display = "none";
  }
  document.getElementById(tabName).style.display = "block";
  
}

/* ============== fetch api ================ */
function getApi() {
  openSpinner();
  fetch(`/people/userinfo/${tabname}`)
    .then((response) => response.json())
    .then((json) => {
      console.log(json);
      return json;
    })
    .then((response) => {
      if (response) {
        hideSpinner();
      }
    })
    .catch(handleErrors);
}

function handleErrors() {
  hideSpinner();
  var tabs = document.querySelectorAll(
    "#overview, #project, #contribution, #activity"
  );
  for (var j = 0; j < tabs.length; j++) {
    tabs[j].innerHTML =
      "<h5>Failed to load data <br/><br/><button onclick='getApi()'>Try again</button></h5>";
  }
}

// Edit name button

var editBtn = document.getElementById("edit-icon");
var editable = document.getElementById("person-name");
var editsave = document.getElementById("edit-confirmation");

editBtn.addEventListener("click", function () {
  editable.contentEditable = "true";
  editable.style =
    "border: 2px solid var(--active); padding:4px 10px; border-radius:25px; transition: 0.4s";
  editsave.innerHTML = "save";
  editsave.style =
    " display: block; background-color:var(--positive); font-size: 0.9rem ; margin-left: 40%; color: var(--primary);";
});

editsave.addEventListener("click", function () {
  editable.contentEditable = "false";
  localStorage.setItem(editable.getAttribute("id"), editable.innerHTML);
  editable.style = "border: 0px ";
});

if (typeof Storage !== "undefined") {
  if (localStorage.getItem("person-name") !== null) {
    editable.innerHTML = localStorage.getItem("person-name");
  }
}
