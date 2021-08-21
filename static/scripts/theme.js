const theme = {
    key: "theme",
    light: "light",
    dark: "dark",
};

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
const accentcolor = {
    [theme.dark]: "#de9846",
    [theme.light]: "#f5d702",
};

const setTheme = (themevalue = theme.light) => {
    localStorage.setItem(theme.key, themevalue);
    window.parent.document
        .getElementById("themecolor")
        .setAttribute("content", [primarycolor[theme.dark],primarycolor[theme.light]].includes(window.parent.document
            .getElementById("themecolor").getAttribute('content'))?primarycolor[themevalue]:accentcolor[themevalue]);
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

getElements("themeswitch").forEach((elem) => {
    elem.addEventListener('click', toggleTheme)
});

addEventListener('keydown',(e)=>{
    if((e.key==='F10'||e.code==='F10'||e.keyCode===121) && e.ctrlKey){
        toggleTheme();
    }
})
