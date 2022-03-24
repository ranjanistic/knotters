const moveBoarding = (current, step = 1) => {
    sessionStorage.setItem("on-boarding-step", current + step - 1);
    getElements("on-boarding-view").forEach((view) => {
        visible(view, view.id != current && view.id == current + step);
    });
    getElement("on-boarding-step-display").innerHTML = `${current + step}/${
        getElements("on-boarding-view").length
    }`;
    window.scrollTo(0, 0);
};
moveBoarding(Number(sessionStorage.getItem("on-boarding-step") || 0));

getElements("moveboarding-action-back").forEach((action) => {
    action.onclick = (_) => {
        moveBoarding(Number(action.getAttribute("data-current")), -1);
    };
});
getElements("moveboarding-action-next").forEach((action) => {
    action.onclick = (_) => {
        moveBoarding(Number(action.getAttribute("data-current")));
    };
});

getElement("on-boarding-finish").onclick = (_) => {
    loader();
    postRequest2({
        path: URLS.ON_BOARDING_UPDATE,
        data: {
            onboarded: true,
        },
    }).then((res) => {
        if (res.code === code.OK) {
            window.location.href =
                "{{request.GET.next}}" ||
                "{{request.user.profile.get_link}}{% if not request.user.profile.on_boarded %}?s=Profile XP increased{% endif %}";
        } else {
            loader(false);
            error(res.error);
        }
    });
};
getElement("profile-pic-upload").onchange = (e) => {
    handleCropImageUpload(
        e,
        "profile-pic-data",
        "profile-pic-output",
        () => {}
    );
};
const onboardAdmireProject = async (projectID) => {
    if (!projectID) return;
    const admirebutton = getElement(`on-board-project-admire-${projectID}`);
    const admire = admirebutton.getAttribute("data-admires") == "0";
    const data = await postRequest2({
        path: setUrlParams(
            URLS.Projects
                ? URLS.Projects.TOGGLE_ADMIRATION
                : URLS.TOGGLE_ADMIRATION,
            projectID
        ),
        data: {
            admire,
        },
        retainCache: true,
    });
    if (data.code !== code.OK) {
        return error(data.error);
    }
    if (admire) {
        message(
            "Admired. Now you'll get to see the latest snapshots of this project on your homepage."
        );
    } else {
        message(
            "Disadmired. You won't get to see the latest snapshots of this project on your homepage."
        );
    }

    admirebutton.setAttribute("data-admires", admire ? 1 : 0);
    admirebutton.classList[admire ? "add" : "remove"]("positive");
    admirebutton.classList[admire ? "remove" : "add"]("primary");
};

let visibleTopicIDs = [];
{% for topid in request.user.profile.getTopicIds %}
visibleTopicIDs.push("{{topid}}");
{% endfor %}
interact(".visible-topics-zone").dropzone({
    accept: "#editable-topic",
    overlap: 0.75,
    ondragactivate: (e) => {},
    ondropactivate: function (event) {
        let dropzoneElement = event.target;
        dropzoneElement.classList.add("tertiary");
    },
    ondragenter: function (event) {
        message("Release to drop!");
    },
    ondragleave: function (event) {
        let draggableElement = event.relatedTarget;
        let dropzoneElement = event.target;
        dropzoneElement.classList.remove("tertiary");
        draggableElement.classList.remove("accent", "negative", "positive");
        draggableElement.classList.add("secondary");

        if (getElement("no-visible-topics-view")) {
            getElement("no-visible-topics-view").style.opacity = 0;
        }
        const topicid = draggableElement.getAttribute("data-topicID");
        visibleTopicIDs = visibleTopicIDs.filter((topid) => topicid != topid);
    },
    ondrop: function (event) {
        let draggableElement = event.relatedTarget;
        const topicid = draggableElement.getAttribute("data-topicID");
        if (
            visibleTopicIDs.length === 5 &&
            !visibleTopicIDs.includes(topicid)
        ) {
            error("Maximum visble topics limit reached");
            draggableElement.classList.remove("secondary", "positive");
            draggableElement.classList.add("negative");
        } else {
            draggableElement.classList.remove(
                "secondary",
                "positive",
                "negative"
            );
            draggableElement.classList.add("accent");
            if (getElement("no-visible-topics-view")) {
                getElement("no-visible-topics-view").style.opacity = 0;
            }
            if (!visibleTopicIDs.includes(topicid))
                visibleTopicIDs.push(topicid);
        }
    },
    ondropdeactivate: function (event) {
        let dropzoneElement = event.target;
        dropzoneElement.classList.remove("tertiary");
    },
});
function dragMoveListener(event) {
    let target = event.target;
    let x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
    let y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;
    target.style.transform = "translate(" + x + "px, " + y + "px)";
    target.style.transition = "transform 0ms ease-in-out";
    target.setAttribute("data-x", x);
    target.setAttribute("data-y", y);
}

window.dragMoveListener = dragMoveListener;
interact(".draggable-topic").draggable({
    inertia: true,
    modifiers: [
        interact.modifiers.restrictRect({
            restriction: "none",
            endOnly: true,
        }),
    ],
    autoScroll: true,
    listeners: { move: dragMoveListener },
});
const saveVisibleTopics = async () => {
    const data = await postRequest2({
        path: URLS.People.TOPICSUPDATE,
        data: {
            visibleTopicIDs,
        },
    });
    if (!data) return;
    if (data.code === code.OK) {
        futuremessage("Changes saved!");
        return window.location.reload();
    }
    error(data.error);
};

getElement("save-visible-topics-action").onclick = (_) => {
    saveVisibleTopics();
};

getElements("onboard-project-admire-action").forEach((action) => {
    action.onclick = (_) => {
        onboardAdmireProject(action.getAttribute("data-projectID"));
    };
});
