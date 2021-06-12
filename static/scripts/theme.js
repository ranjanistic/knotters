const theme = {
    key: "theme",
    light: "light",
    dark: "dark",
};

getElements("themeswitch").forEach((elem) => {
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
    window.parent.document.documentElement.setAttribute(
        "data-theme",
        themevalue
    );
    Array.from(document.getElementsByClassName("darkimg")).forEach((img) => {
        img.src = `/static/graphics/${img.getAttribute("data-name")}${
            themevalue === theme.light ? "" : "-dark"
        }.${img.getAttribute("data-ext")}`;
    });
};

if (!localStorage.getItem(theme.key)) {
    localStorage.setItem(theme.key, theme.light);
}

setTheme(localStorage.getItem(theme.key));
