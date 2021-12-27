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
    Array.from(getElements("darkimg")).forEach((img) => {
        const parts = img.tagName.toLowerCase()==='link'?img.href.split('.'):img.src.split('.')
        img.tagName.toLowerCase()==='link'
            ?img.href = String(img.href).replace(window.location.origin,'').replace(`${themevalue === theme.dark ? "" : "-dark"}.${parts[parts.length-1]}`,`${themevalue === theme.light ? "" : "-dark"}.${parts[parts.length-1]}`)
            :img.src = String(img.src).replace(window.location.origin,'').replace(`${themevalue === theme.dark ? "" : "-dark"}.${parts[parts.length-1]}`,`${themevalue === theme.light ? "" : "-dark"}.${parts[parts.length-1]}`)
    });
    Array.from(getElements("darkimg-invert")).forEach((img) => {
        const parts = img.tagName.toLowerCase()==='link'?img.href.split('.'):img.src.split('.')
        img.tagName.toLowerCase()==='link'
            ?img.href = String(img.href).replace(window.location.origin,'').replace(`${themevalue === theme.light ? "" : "-dark"}.${parts[parts.length-1]}`,`${themevalue === theme.dark ? "" : "-dark"}.${parts[parts.length-1]}`)
            :img.src = String(img.src).replace(window.location.origin,'').replace(`${themevalue === theme.light ? "" : "-dark"}.${parts[parts.length-1]}`,`${themevalue === theme.dark ? "" : "-dark"}.${parts[parts.length-1]}`)
    });
    Array.from(getElements("darkimg-static")).forEach((img) => {
        const parts = img.tagName.toLowerCase()==='link'?img.href.split('.'):img.src.split('.')
        img.tagName.toLowerCase()==='link'
            ?img.href = String(img.href).replace(window.location.origin,'').replace(`-dark.${parts[parts.length-1]}`,`.${parts[parts.length-1]}`).replace(`.${parts[parts.length-1]}`,`-dark.${parts[parts.length-1]}`)
            :img.src = String(img.src).replace(window.location.origin,'').replace(`-dark.${parts[parts.length-1]}`,`.${parts[parts.length-1]}`).replace(`.${parts[parts.length-1]}`,`-dark.${parts[parts.length-1]}`)
    });
};

if (!localStorage.getItem(theme.key)) {
  sessionStorage.setItem('device-theme',1)
   if (window.matchMedia && window.matchMedia(`(prefers-color-scheme: ${theme.dark})`).matches) {
     localStorage.setItem(theme.key, theme.dark);
   } else {
     localStorage.setItem(theme.key, theme.light);
   }
} else {
    sessionStorage.setItem('device-theme', 0)
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
if(window.matchMedia) {
    window.matchMedia(`(prefers-color-scheme: ${theme.dark})`).addEventListener('change', e => {
        localStorage.setItem(theme.key, e.matches? theme.dark: theme.light);
        setTheme(localStorage.getItem(theme.key))
    });
}
