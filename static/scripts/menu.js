const mobile_menu = document.querySelector('.mobile-nav');

const openMenu = (open = true) => {
  if (open) {
    mobile_menu.classList.add('is-active');
  } else {
    mobile_menu.classList.remove('is-active');
  }
};

//Open menu when menu button is clicked
var menuActions = getElements('menu-action');
menuActions.forEach((menuAction) => {
  menuAction.addEventListener('click', () => {
    openMenu();
  });
});

//Close menu when close button is clicked
var menuCloseActions = getElements('menu-close-btn');
menuCloseActions.forEach((menuCloseAction) => {
  menuCloseAction.addEventListener('click', () => {
    openMenu(false);
  });
});

//Close menu when clicked outside the menu
window.addEventListener('mouseup', function (event) {
  let box = document.getElementById('nav-menu');
  if (!Array.from(box.getElementsByTagName("*")).includes(event.target)) {
    openMenu(false);
  }
});

getElements('accordion').forEach((acc) => {
  acc.addEventListener("click", function () {
    let hoverClass = Array.from(acc.classList).find((currentClass) => currentClass.startsWith('hover-'));
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
