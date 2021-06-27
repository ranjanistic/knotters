subLoader(true);
serviceWorkerRegistration();

document.addEventListener("DOMContentLoaded", () => {
    getElementsByTag("form").forEach((form) => {
        form.addEventListener("submit", (e) => {
            if (form.classList.contains("no-auto")) {
                e.preventDefault();
            } else {
                subLoader(true);
            }
        });
    });
    getElementsByTag("a").forEach((a) => {
        if (a.getAttribute("href")&&!a.getAttribute("href").startsWith('#')&&!a.getAttribute("target")) {
            a.addEventListener("click", (e) => {
                subLoader(true);
            });
        }
    });
    getElements("href").forEach((href) => {
        href.addEventListener("click", (e) => {
            subLoader(true);
            window.location.href = href.getAttribute("data-href");
        });
    });
    getElementsByTag("button").forEach((button) => {
        if (button.title) {
            let mPressTimer;
            button.addEventListener("touchstart", (e) => {
                mPressTimer = window.setTimeout(() => {
                    alertify.set("notifier", "position", "bottom-right");
                    alertify.message(button.title);
                }, 500);
                button.addEventListener("touchend", (e) => {
                    clearTimeout(mPressTimer);
                });
            });
        }
    });
    getElementsByTag("i").forEach((icon) => {
        if (icon.classList && icon.title) {
            let mPressTimer;
            icon.addEventListener("touchstart", (e) => {
                mPressTimer = window.setTimeout(() => {
                    alertify.set("notifier", "position", "bottom-right");
                    alertify.message(icon.title);
                }, 500);
                icon.addEventListener("touchend", (e) => {
                    clearTimeout(mPressTimer);
                });
            });
        }
    });
});

window.addEventListener("load",()=>{  
    subLoader(false);
})
