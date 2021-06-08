function openTab(tabName) {
  var i;
  var x = document.getElementsByClassName("tab");
  for (i = 0; i < x.length; i++) {
    x[i].style.display = "none";
  }
  document.getElementById(tabName).style.display = "block";
}

/* =========== Preloader ==============*/

function openSpinner() {
  document.getElementById("loader").style.display = "block";
}

function hideSpinner() {
  document.getElementById("loader").style.display = "none";
}

/* ============== fetch api ================ */
function getApi() {
  openSpinner();
  fetch("https://jsonplaceholder.typicode.com/todos/1")
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
    .catch(function (err) {
      hideSpinner();
      document.querySelector("#overview").innerHTML =
        "<h5>Failed to load data <br/><br/><button onclick='getApi()' >Try again</button></h5>";
      document.querySelector("#project").innerHTML =
        "<h5>Failed to load data <br/><br/><button onclick='getApi()' >Try again</button></h5>";
      document.querySelector("#contribution").innerHTML =
        "<h5>Failed to load data <br/><br/><button onclick='getApi()' >Try again</button></h5>";
      document.querySelector("#activity").innerHTML =
        "<h5>Failed to load data <br/><br/><button onclick='getApi()' >Try again</button></h5>";
      console.log("error: " + err);
    });
}
