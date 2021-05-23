const theme = {
  key: "theme",
  light: "light",
  dark: "dark",
};

Array.from(document.getElementsByClassName("themeswitch")).forEach((elem) => {
  elem.onclick = (_) => toggleTheme();
});

const toggleTheme = () => {
  isLight() ? setDark() : setLight();
};
const setDark = () => {
  setTheme(theme.dark);
};
const setLight = () => {
  setTheme(theme.light);
};
const isLight = () => {
  return getTheme() == theme.light;
};
const isDark = () => {
  return getTheme() == theme.dark;
};

const getTheme = () => {
  return localStorage.getItem(theme.key);
};

const primarycolor = {
  [theme.dark]: "#000000",
  [theme.light]: "#ffffff",
};

const setTheme = (themevalue = theme.light) => {
  localStorage.setItem(theme.key, themevalue);
  window.parent.document
    .getElementById("themecolor")
    .setAttribute("content", primarycolor[themevalue]);
  document.documentElement.setAttribute("data-theme", themevalue);
  window.parent.document.documentElement.setAttribute("data-theme", themevalue);
};

localStorage.getItem(theme.key)
  ? document.documentElement.setAttribute(
      "data-theme",
      localStorage.getItem(theme.key)
    )
  : localStorage.setItem(theme.key, theme.light);
