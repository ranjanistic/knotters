class Theme {
    key = KEY.current_theme;
    light = "light";
    dark = "dark";

    toggleTheme = () => {
        this.isLight() ? this.setDark() : this.setLight();
    };
    setDark = () => {
        this.setTheme(this.dark);
    };
    setLight = () => {
        this.setTheme(this.light);
    };
    isLight = () => {
        return this.getTheme() == this.light;
    };
    isDark = () => {
        return this.getTheme() == this.dark;
    };

    getTheme = () => {
        return localStorage.getItem(KEY.current_theme);
    };

    setTheme = (themevalue = this.light) => {
        localStorage.setItem(KEY.current_theme, themevalue);
        window.parent.document
            .getElementById("themecolor")
            .setAttribute(
                "content",
                COLOR.getColorByTheme(
                    window.parent.document
                        .getElementById("themecolor")
                        .getAttribute("content").trim(),
                    themevalue
                ) || COLOR.primary()
            );
        document.documentElement.setAttribute("data-theme", themevalue);
        window.parent.document.documentElement.setAttribute(
            "data-theme",
            themevalue
        );
        Array.from(getElements("darkimg")).forEach((img) => {
            const parts =
                img.tagName.toLowerCase() === "link"
                    ? img.href.split(".")
                    : img.src.split(".");
            img.tagName.toLowerCase() === "link"
                ? (img.href = String(img.href)
                      .replace(window.location.origin, "")
                      .replace(
                          `${themevalue === this.dark ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`,
                          `${themevalue === this.light ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`
                      ))
                : (img.src = String(img.src)
                      .replace(window.location.origin, "")
                      .replace(
                          `${themevalue === this.dark ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`,
                          `${themevalue === this.light ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`
                      ));
        });
        Array.from(getElements("darkimg-invert")).forEach((img) => {
            const parts =
                img.tagName.toLowerCase() === "link"
                    ? img.href.split(".")
                    : img.src.split(".");
            img.tagName.toLowerCase() === "link"
                ? (img.href = String(img.href)
                      .replace(window.location.origin, "")
                      .replace(
                          `${themevalue === this.light ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`,
                          `${themevalue === this.dark ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`
                      ))
                : (img.src = String(img.src)
                      .replace(window.location.origin, "")
                      .replace(
                          `${themevalue === this.light ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`,
                          `${themevalue === this.dark ? "" : "-dark"}.${
                              parts[parts.length - 1]
                          }`
                      ));
        });
        Array.from(getElements("darkimg-static")).forEach((img) => {
            const parts =
                img.tagName.toLowerCase() === "link"
                    ? img.href.split(".")
                    : img.src.split(".");
            img.tagName.toLowerCase() === "link"
                ? (img.href = String(img.href)
                      .replace(window.location.origin, "")
                      .replace(
                          `-dark.${parts[parts.length - 1]}`,
                          `.${parts[parts.length - 1]}`
                      )
                      .replace(
                          `.${parts[parts.length - 1]}`,
                          `-dark.${parts[parts.length - 1]}`
                      ))
                : (img.src = String(img.src)
                      .replace(window.location.origin, "")
                      .replace(
                          `-dark.${parts[parts.length - 1]}`,
                          `.${parts[parts.length - 1]}`
                      )
                      .replace(
                          `.${parts[parts.length - 1]}`,
                          `-dark.${parts[parts.length - 1]}`
                      ));
        });
    };
}

const THEME = new Theme();

class Color {
    constructor(theme = null) {
        this.theme = theme;
    }
    primary = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#ffffff" : "#000000";
    primaryText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#000000" : "#eaeaea";
    secondary = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#000000" : "#05050a";
    secondaryText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#ffffff" : "#ffffff";
    tertiary = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#efefef" : "#151313";
    tertiaryText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#141414" : "#ffffff";
    accent = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#f5d702" : "#de9846";
    accentText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#000000" : "#000000";
    active = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#12e49d" : "#4dbb96";
    activeText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#000000" : "#000000";
    positive = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#1657ce" : "#7796d0";
    positiveText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#ffffff" : "#000000";
    negative = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#cc352a" : "#ce6862";
    negativeText = (th = this.theme || THEME.getTheme()) =>
        th == THEME.light ? "#ffffff" : "#000000";
    deadText = (th = this.theme || THEME.getTheme()) => "#868686c7";

    getColorByTheme = (color, theme) => {
        switch (color) {
            case this.primary(THEME.light):
                return this.primary(theme);
            case this.primary.name:
                return this.primary(theme);
            case this.primary(THEME.dark):
                return this.primary(theme);
            case this.primaryText(THEME.light):
                return this.primaryText(theme);
            case this.primaryText(THEME.dark):
                return this.primaryText(theme);
            case this.secondary(THEME.light):
                return this.secondary(theme);
            case this.secondary.name:
                return this.secondary(theme);
            case this.secondary(THEME.dark):
                return this.secondary(theme);
            case this.secondaryText(THEME.light):
                return this.secondaryText(theme);
            case this.secondaryText(THEME.dark):
                return this.secondaryText(theme);
            case this.tertiary(THEME.light):
                return this.tertiary(theme);
            case this.tertiary.name:
                return this.tertiary(theme);
            case this.tertiary(THEME.dark):
                return this.tertiary(theme);
            case this.tertiaryText(THEME.light):
                return this.tertiaryText(theme);
            case this.tertiaryText(THEME.dark):
                return this.tertiaryText(theme);
            case this.accent(THEME.light):
                return this.accent(theme);
            case this.accent.name:
                return this.accent(theme);
            case this.accent(THEME.dark):
                return this.accent(theme);
            case this.accentText(THEME.light):
                return this.accentText(theme);
            case this.accentText(THEME.dark):
                return this.accentText(theme);
            case this.active(THEME.light):
                return this.active(theme);
            case this.active.name:
                return this.active(theme);
            case this.active(THEME.dark):
                return this.active(theme);
            case this.activeText(THEME.light):
                return this.activeText(theme);
            case this.activeText(THEME.dark):
                return this.activeText(theme);
            case this.positive(THEME.light):
                return this.positive(theme);
            case this.positive.name:
                return this.positive(theme);
            case this.positive(THEME.dark):
                return this.positive(theme);
            case this.positiveText(THEME.light):
                return this.positiveText(theme);
            case this.positiveText(THEME.dark):
                return this.positiveText(theme);
            case this.negative(THEME.light):
                return this.negative(theme);
            case this.negative.name:
                return this.negative(theme);
            case this.negative(THEME.dark):
                return this.negative(theme);
            case this.negativeText(THEME.light):
                return this.negativeText(theme);
            case this.negativeText(THEME.dark):
                return this.negativeText(theme);
            case this.deadText(THEME.light):
                return this.deadText(theme);
            case this.deadText(THEME.dark):
                return this.deadText(theme);
            default:
                return color;
        }
    };
}
const COLOR = new Color();

const primarycolor = {
    [THEME.dark]: COLOR.primary(THEME.dark),
    [THEME.light]: COLOR.primary(THEME.light),
};

const accentcolor = {
    [THEME.dark]: COLOR.accent(THEME.dark),
    [THEME.light]: COLOR.accent(THEME.light),
};

if (!localStorage.getItem(KEY.current_theme)) {
    sessionStorage.setItem("device-theme", 1);
    if (
        window.matchMedia &&
        window.matchMedia(`(prefers-color-scheme: ${THEME.dark})`).matches
    ) {
        localStorage.setItem(KEY.current_theme, THEME.dark);
    } else {
        localStorage.setItem(KEY.current_theme, THEME.light);
    }
} else {
    sessionStorage.setItem("device-theme", 0);
}

THEME.setTheme(localStorage.getItem(KEY.current_theme));

getElements("themeswitch").forEach((elem) => {
    elem.addEventListener("click", THEME.toggleTheme);
});

addEventListener("keydown", (e) => {
    if (
        (e.key === "F10" || e.code === "F10" || e.keyCode === 121) &&
        e.ctrlKey
    ) {
        THEME.toggleTheme();
    }
});
if (window.matchMedia) {
    window
        .matchMedia(`(prefers-color-scheme: ${THEME.dark})`)
        .addEventListener("change", (e) => {
            localStorage.setItem(
                KEY.current_theme,
                e.matches ? THEME.dark : THEME.light
            );
            THEME.setTheme(localStorage.getItem(KEY.current_theme));
        });
}

const isDark = THEME.isDark;
const toggleTheme = THEME.toggleTheme;
const setDark = THEME.setDark;
const setLight = THEME.setLight;
const isLight = THEME.isLight;
const setTheme = THEME.setTheme;
const getTheme = THEME.getTheme;
