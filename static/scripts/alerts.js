const loader = (show = true) => {
    if (show) {
        getElements("swal2-container").forEach((e) => (e.style.zIndex = 1060));
    }
    visibleElement("viewloader", show);
};
const subLoader = (show = true) => {
    if (show) {
        getElements("swal2-container").forEach((e) => (e.style.zIndex = 1060));
    }
    visibleElement("subloader", show);
};
subLoader(true);

const loaders = (show = true) => {
    loader(show);
    subLoader(show);
};

const message = (msg = "", onOpen=(toast)=>{}) => {
    Swal.mixin({
        toast: true,
        position: "bottom-start",
        showConfirmButton: false,
        iconColor: "#000",
        timer: Math.max(msg.split(" ").length * 400, 3000),
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener("mouseenter", Swal.stopTimer);
            toast.addEventListener("mouseleave", Swal.resumeTimer);
            getElements("swal2-container").forEach(
                (e) => (e.style.zIndex = 999999999)
            );
            onOpen(toast)
        },
    }).fire({
        icon: "info",
        title: msg,
    });
};

const error = (msg = STRING.default_error_message, force = false) => {
    if (msg !== STRING.default_error_message || force) {
        Swal.mixin({
            toast: true,
            position: "bottom-end",
            showConfirmButton: false,
            iconColor: "#000",
            timer: Math.max(msg.split(" ").length * 400, 3000),
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener("mouseenter", Swal.stopTimer);
                toast.addEventListener("mouseleave", Swal.resumeTimer);
                getElements("swal2-container").forEach(
                    (e) => (e.style.zIndex = 999999999)
                );
            },
        }).fire({
            icon: "error",
            title: msg || STRING.default_error_message,
        });
    }
};

const success = (msg = "Success") => {
    Swal.mixin({
        toast: true,
        position: "top-end",
        showConfirmButton: false,
        iconColor: "#fff",
        timer: Math.max(msg.split(" ").length * 400, 3000),
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener("mouseenter", Swal.stopTimer);
            toast.addEventListener("mouseleave", Swal.resumeTimer);
            getElements("swal2-container").forEach(
                (e) => (e.style.zIndex = 999999999)
            );
        },
    }).fire({
        icon: "success",
        title: msg,
    });
};

const loaderHTML = (loaderID = "loader") =>
    `<span class="w3-padding-small"><div class="loader" id="${loaderID}"></div></span>`;
const loadErrorHTML = (
    retryID = "retryload"
) => `<div class="w3-center w3-padding-32">
<i class="negative-text material-icons w3-jumbo">error</i>
<h3>Oops. Something wrong here?</h3><button class="primary" id="${retryID}">Retry</button></div></div>`;

const betaAlert = () => {
    if (window.location.host.startsWith("beta.") || window.location.host.startsWith("localhost")|| window.location.host.startsWith("127.0.0.1")) {
        Swal.fire({
            title: `This is ${APPNAME}`,
            html: `
            <h5>
            Welcome to ${APPNAME}, the pre-stable version of Knotters.<br/>
            New features become available here before Knotters.<br/>
            You'll have to create an account here separately from Knotters. None of the information at Knotters will be made available here.
            <br/>
            By continuing, you accept that for any of your data loss at Knotters Beta due to any error, you will solely be responsible.
            </h5>
            `,
            confirmButtonText: "Go to Knotters",
            cancelButtonText: `Stay in ${APPNAME}`,
            showCancelButton: true,
            focusConfirm: false,
            allowOutsideClick: false,
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = window.location.href.replace(
                    "//beta.",
                    "//"
                );
            } else {
                window.sessionStorage.setItem("beta-alerted", 1);
                message(`Remember, you're using ${APPNAME}!`);
            }
        });
    }
};

const connectWithGithub = (next = URLS.ROOT, oncancel = (_) => {}) => {
    Swal.fire({
        title: "Github ID Required",
        html:`<div class="w3-row w3-padding">
        <h4>Your Github identity must be linked with Knotters for this action.</h4>
        </div>`,
        imageUrl: '/static/graphics/thirdparty/github.png',
        confirmButtonText: `${Icon('open_in_new')}Link Github Account`,
        cancelButtonText: "Leave it",
        showCancelButton: true,
    }).then((res)=>{
        if(res.isConfirmed){
            return window.location.href=setUrlQueries(`${URLS.Auth.GITHUB}login/`,{process:'connect',next:setUrlQueries(URLS.REDIRECTOR, {n:next})})
        } else {
            oncancel()
        }
    })
};

const troubleShootingInfo =()=>{
    Swal.fire({
        title: "Troubleshooting",
        html: `
            <div class="w3-row w3-left">
            <h5>If you are facing problems during normal usage of ${APPNAME}, then any or all of the following steps might help you out.</h5>
            <br/>
            <strong class="text-medium">
            <a onclick="miniWindow('https://www.google.com/search?q=clear+browser+cache')">Clear your browser's cache</a>
            <br/><br/>
            <a onclick="miniWindow('https://www.google.com/search?q=how+to+clear+specific+site+data')">Clear site data</a> from your browser's settings
            ${authenticated?'<br/>(this will log you out)':''}
            <br/><br/>
            <a onclick="miniWindow('https://www.google.com/search?q=hard+reload+site')">Force reload current page</a>
            </span>
            </div>
        `,
        confirmButtonText: "Problem solved!",
        denyButtonText: "I still have problems",
        showCancelButton: false,
        showDenyButton: true,
        preConfirm: () => {
        }
    }).then((res)=>{
        if(res.isConfirmed){
            message("Glad we could help 😊! Do not hesitate to contact us anytime.")
        } else if(res.isDenied){
            window.scrollTo(0,document.body.scrollHeight);
            message("We're sorry to hear that. You may submit a report, or reach us via our social channels or email. Click here to report.", (toast)=>{
                toast.onclick=_=>reportFeedbackView()
            })
        }
    })
}

const blockUserView = ({
    userID ='',
    username = '',
    userDP = null,
}) => {
    Swal.fire({
        title:`Block ${username}?`,
        imageUrl: userDP,
        imageWidth: 100,
        html:`<h6>Are you sure you want to ${NegativeText(`block ${username}`)}?
        <br/>You both will be invisible to each other on ${APPNAME},<br/>including all associated activities.
        <br/>You can unblock them anytime from your profile's privacy settings.
        </h6>`,
        showDenyButton: true,
        confirmButtonText: 'No, wait!',
        denyButtonText: 'Yes, block!'
    }).then(async(res)=>{
        if(res.isDenied){
            loader()
            message('Blocking...')
            const data = await postRequest(URLS.People?URLS.People.BLOCK_USER:URLS.BLOCK_USER,{
                userID
            })
            if(!data) return loader(false)
            if(data.code===code.OK){
                futuremessage(`Blocked ${username}.`)
                return window.location.replace(ROOT)
            }
            loader(false)
            error(data.error)
        }
    })
    
}