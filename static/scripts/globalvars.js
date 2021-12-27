const KEY = {
    appUpdated: "app-updated",
    navigated: "navigated",
    futureMessage: "future-message",
    deferupdate: "deferupdate",
    previewImageInfo: "preview-image-info"
};
const Key = KEY;

const CODE = {
    OK: "OK",
    NO: "NO",
    LEFT: "left",
    RIGHT: "right",
};
const code = CODE;

const THEME = {
    key: "theme",
    light: "light",
    dark: "dark",
};
const theme = THEME;

const COLOR = {
    primary: (th = getTheme()) => (th == THEME.light ? "#ffffff" : "#000000"),
    primaryText: (th = getTheme()) =>
        th == THEME.light ? "#000000" : "#eaeaea",
    secondary: (th = getTheme()) => (th == THEME.light ? "#000000" : "#05050a"),
    secondaryText: (th = getTheme()) =>
        th == THEME.light ? "#ffffff" : "#ffffff",
    tertiary: (th = getTheme()) => (th == THEME.light ? "#efefef" : "#151313"),
    tertiaryText: (th = getTheme()) =>
        th == THEME.light ? "#141414" : "#ffffff",
    accent: (th = getTheme()) => (th == THEME.light ? "#f5d702" : "#de9846"),
    accentText: (th = getTheme()) =>
        th == THEME.light ? "#000000" : "#000000",
    active: (th = getTheme()) => (th == THEME.light ? "#12e49d" : "#4dbb96"),
    activeText: (th = getTheme()) =>
        th == THEME.light ? "#000000" : "#000000",
    positive: (th = getTheme()) => (th == THEME.light ? "#1657ce" : "#7796d0"),
    positiveText: (th = getTheme()) =>
        th == THEME.light ? "#ffffff" : "#000000",
    negative: (th = getTheme()) => (th == THEME.light ? "#cc352a" : "#ce6862"),
    negativeText: (th = getTheme()) =>
        th == THEME.light ? "#ffffff" : "#000000",
    deadText: (th = getTheme()) => "#868686c7",
};

const primarycolor = {
    [THEME.dark]: COLOR.primary(THEME.dark),
    [THEME.light]: COLOR.primary(THEME.light),
};

const accentcolor = {
    [THEME.dark]: COLOR.accent(THEME.dark),
    [THEME.light]: COLOR.accent(THEME.light),
};

let __appInstallPromptEvent = null;
