const mobile_menu = document.querySelector('.mobile-nav');
var menuActions = getElements('menu-action');

//Open menu when menu button is clicked
menuActions.forEach((menuAction)=>{
    menuAction.addEventListener('click',()=>{
        mobile_menu.classList.add('is-active');
    });
});

var menuActions = getElements('menu-close-btn');

//Close menu when close button is clicked
menuActions.forEach((menuAction)=>{
    menuAction.addEventListener('click',()=>{
        mobile_menu.classList.remove('is-active');
    });
});

//Close menu when clicked outside the menu
window.addEventListener('mouseup', function(event){
	let box = document.getElementById('nav-menu');
  if(!Array.from(box.getElementsByTagName("*")).includes(event.target)){
    mobile_menu.classList.remove('is-active');
  }
});

getElements('accordion').forEach((acc)=>{
  acc.addEventListener("click", function() {
    let hoverClass = Array.from(acc.classList).find((currentClass)=>currentClass.startsWith('hover-'));
    let themeClass = hoverClass.split('-')[1];
    acc.classList.toggle(themeClass);

    let panel = acc.nextElementSibling;
    if (panel.style.display === "block") {
      panel.style.display = "none";
    } else {
      panel.style.display = "block";
    }
  });
});
