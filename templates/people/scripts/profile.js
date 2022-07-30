{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

{% comment %} 'person' is an instance of User (request.user) {% endcomment %}
const userID = "{{ person.getID }}";
const selfProfile = "{{self}}" == "True" ? activeuser : false;
const isModerator = "{{person.profile.is_moderator}}" == "True";
const isMentor = "{{person.profile.is_mentor}}" == "True";
const isManager = "{{is_manager}}" == "True";
const isAdmirer = "{{is_admirer}}" == "True";
const theme = "{{person.profile.theme}}";
const tabindex =
    Number("{{request.GET.tab}}" || -2) > -1
        ? Number("{{request.GET.tab}}")
        : false;
{% if is_manager %}
const mgmID = "{{person.profile.manager_id}}";
{% endif %}

{% if person.profile.is_active %}
    {% if self %}
    console.log("hhhhhh")
getElement("sociallinks-add").onclick = (_) => {
    const parent = getElement("edit-sociallinks-inputs");
    if (parent.childElementCount === 5)
        return message("Maximun URLs limit reached");
    const linkNumber = parent.childElementCount + 1;
    const newChild = document.createElement("div");
    newChild.innerHTML = `
              <input class="wide" type="url" inputmode="url" placeholder="Link to anything relevant" name="sociallink${linkNumber}" id=sociallink${linkNumber} /><br/><br/>
          `;
    parent.insertBefore(newChild, parent.childNodes[0]);
};


        {% if is_manager and has_ghID %}
        console.log("hello")
getElement("link-gh-org-mgm").onclick = (_) => {
    Swal.fire({
        title: "Link GitHub organization",
        html: `
            Please make sure that you are allowed to represent your organization on Knotters by your administrators.</br></br>
            <div class="w3-row">
                <select id='selected-org-id' class="pallete-slab">
              {% for org in request.user.profile.get_ghOrgsIDName %}
                  <option value="{{org.id}}">{{org.name}}</option>
              {% endfor %}
                </select>
            </div>
              `,
        icon: "",
        confirmButtonText: "Link with profile",
        showCancelButton: true,
        {% if gh_orgID %}
        showDenyButton: true,
        denyButtonText: "Unlink organization",
        {% endif %}
        preConfirm: () => {
            return getElement("selected-org-id").value;
        },
    }).then(async (result) => {
        if (result.isConfirmed) {
            const data = await postRequest2({
                path: URLS.Auth.CHANGE_GHORG,
                data: {
                    newghorgID: result.value,
                },
            });
            if (data && data.code == CODE.OK) {
                success("GitHub organization linked");
                return refresh({});
            }
            error(data.error);
        } else if (result.isDenied) {
            const data = await postRequest2({
                path: URLS.Auth.CHANGE_GHORG,
                data: {
                    newghorgID: false,
                },
            });
            if (data && data.code == CODE.OK) {
                message("GitHub organization unlinked");
                return refresh({});
            }
            error(data.error);
        }
    });
};
        {% endif %}
    {% else %}
        {% if request.user.is_authenticated %}
getElement("block-account").onclick = async () => {
    blockUserView({
        userID,
        username: "{{person.profile.getName}}",
        userDP: "{{person.profile.getDP}}",
    });
};
getElement("report-account").onclick = async () => {
    await violationReportDialog(
        URLS.REPORT_USER,
        {
            userID: "{{person.get_id}}",
        },
        "{{person.profile.getName}}",
        URLS.REPORT_CATEGORIES
    );
};
            {% if request.GET.admire == '1' and not is_admirer %}
getElement("toggle-admiration").click();
            {% endif %}
            {% if request.GET.admire == '0' and is_admirer %}
getElement("toggle-admiration").click();
            {% endif %}
        {% endif %}
    {% endif %}
getElement("show-admirations").onclick = async (_) => {
    Swal.fire({
        html: await getRequest2({
            path: setUrlParams(URLS.ADMIRATIONS, userID),
        }),
        title: "<h4 class='positive-text'>Admirers</h4>",
    });
};
{% elif not person.profile.is_active %}
try {
    console.log("hhhhhh")
    getElement("reactivateaccount").onclick = async () => {
        loaders();
        message("Reactivating your account...");
        const data = await postRequest(URLS.Auth.ACCOUNTACTIVATION, {
            activate: true,
        });
        if (data.code === code.OK) {
            success(`{% trans "Your account has been reactivated" %}`);
            return await logOut();
        }
        subLoader(false);
        loader(false);
        error(data.error);
    };
} catch {}
{% endif %}

