{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

const projectID = "{{ project.get_id }}";
const selfProject = "{{iscreator}}"==='True';
const ismoderator = false;
const iscreator = selfProject;
const iscocreator = "{{iscocreator}}"==='True';
const projectcolor = getComputedStyle(document.querySelector(':root')).getPropertyValue('--positive');

{% if not project.suspended %}
{% if iscreator %}
    {% if project.can_delete %}
    getElement('delete-project').onclick=_=>{
        Swal.fire({
            title: '{% trans "Delete Project" %}',
            html: `<h4>Are you sure you want to delete your project '{{project.name}}' ({{project.nickname}})? All associated data will also be deleted, and
                    this action is permanent.</h4>`,
            showDenyButton: true,
            showCancelButton: false,
            denyButtonText: 'Yes, DELETE',
            confirmButtonText: 'No, wait!',
        }).then(async(result)=>{
            if(result.isDenied){
                loader()
                const data = await postRequest2({path:setUrlParams(URLS.TRASH,projectID)})
                if(!data) return loader(false)
                if(data.code===code.OK){
                    futuremessage('{{project.nickname}} was deleted.')
                    return window.location.href=URLS.PROJECTS
                }
                error(data.error)
                loader(false)
            } else {
                message('Phew!')
            }
        })
    }
    {% endif %}
    {% if project.can_invite_owner %}
    getElement('transfer-project').onclick=(e)=>{
        Swal.fire({
            title: 'Transfer project',
            html: `<h6>Transfer project '{{project.nickname}}' to another user.<br/>
            Invite the new owner by their email to transfer project.</h6>
            <br/>
            <input class="wide" type="email" autocomplete="email" placeholder="New email address" id="transfer-project-new-email" />
            `,
            showCancelButton: true,
            confirmButtonText: 'Send Invite',
            cancelButtonText: 'Cancel',
            showLoaderOnConfirm: true,
            preConfirm: async () => {
                let email = getElement("transfer-project-new-email").value.trim()
                if(email) return email
                error('New email address required')
                return false
            }
        }).then(async (result) => {
            if (result.isConfirmed) {
                message("Sending invitation...");
                const data = await postRequest2({
                    path: URLS.INVITE_PROJECT_OWNER,
                    data: {
                        action: 'create',
                        projectID,
                        email: result.value,
                    }
                })
                if(data.code===code.OK){
                    futuremessage("Invitation sent.")
                    return window.location.reload()
                }
                error(data.error)
            }
        })
    }
    {% elif project.under_invitation %}
        getElement('delete-project-invitation').onclick=async(e)=>{
            message("Deleting invitation...");
            const data = await postRequest2({
                path: URLS.INVITE_PROJECT_OWNER,
                data: {
                    action: 'remove',
                    projectID,
                }
            })
            if(data.code===code.OK){
                futuremessage("Invitation cancelled")
                return window.location.reload()
            }
            error(data.error)
        }
    {% endif %}
    {% if project.can_request_verification %}
    getElement('request-verification').onclick=async(e)=>{
        Swal.fire({
            title: 'Request verification',
            html: `
                <strong>
               {% if project.is_submission and project.submission.is_winner %}
                Since your project is a winner submission of {{project.submission.competition}} competition, it will be reviewed by moderator of the competition.
                If the moderator is not available, another moderator will be assigned. Assigned moderator will also be aware of your winner status.
               {% else %}
                By requesting verification, you are submitting your project for review by an appropriate moderator at {{APPNAME}}.
               {% endif %}<br/>
                If approved, your project will no longer exist as Quick project, and your linked repository will be removed from it,
                and your project will become a verified project on Knotters with a separate repository from Knotters.
                License will remain the same.</strong>
                <br/><br/>
                Project detail for moderator to read<br/>
                <textarea class="wide" placeholder="Reason for verification" id="request-verification-reason"></textarea>
                <br/>
                Maximum days to review<br/>
                <input type="number" class="wide" min="1" max="15" placeholder="Stale days (min 1, max 15)" value="3" id="request-verification-stale-days" />
                <br/>
                {% if request.user.profile.is_manager %}
                Use internal moderator
                <input type="checkbox" id="request-verification-internal" />
                {% endif %}
            `,
            showCancelButton: true,
            confirmButtonText: 'Send Request',
            cancelButtonText: 'Cancel',
            preConfirm: async () => {
                const requestData = getElement('request-verification-reason').value.trim()
                if(!requestData) {
                    error('Reason required')
                    return false
                }
                const stale_days = getElement('request-verification-stale-days').value
                if(!stale_days) {
                    error('Stale days required')
                    return false
                }
                return {
                    requestData,
                    stale_days:Number(stale_days), 
                    {% if request.user.profile.is_manager %}
                    internalMod:getElement('request-verification-internal').checked
                    {% endif %}
                }
            }
        }).then(async(result)=>{
            if(result.isConfirmed){
                loader()
                message("Sending request...");
                const data = await postRequest2({
                    path: setUrlParams(URLS.FREE_VERIFICATION_REQUEST),
                    data: {
                        action: 'create',
                        projectID,
                        requestData: result.value.requestData,
                        stale_days:result.value.stale_days,
                        useInternalMods:result.value.internalMod||false,
                       {% if project.is_submission and project.submission.is_winner %}
                        winnerVerification: true,
                       {% endif %}
                    }
                })
                if(data.code===CODE.OK){
                    futuremessage("Verification request sent.")
                    return window.location.reload()
                }
                loader(false)
                error(data.error)
            }
        })
    }
        {% if request.GET.verification %}
            getElement('request-verification').click()
        {% endif %}
    {% elif project.under_verification_request %}
    getElement('cancel-verification-request').onclick=async(e)=>{
        Swal.fire({
            title: 'Cancel verification request',
            html: `
                <strong>By cancelling verification request, you are cancelling your project's verification request.
                The assigned moderator will no longer be able to review your project.
                Please note that if the project has already been approved before you could cancel the request,
                then cancellation will not be possible, and this quick project may already have been deleted.</strong>
            `,
            showCancelButton: false,
            showDenyButton: true,
            confirmButtonText: 'No, wait!',
            denyButtonText: 'Cancel verification',
        }).then(async(result)=>{
            if(result.isDenied){
                loader()
                message("Cancelling verification request...");
                const data = await postRequest2({
                    path: setUrlParams(URLS.FREE_VERIFICATION_REQUEST),
                    data: {
                        action: 'remove',
                        projectID,
                    }
                })
                if(data.code===CODE.OK){
                    futuremessage("Verification request cancelled.")
                    return window.location.reload()
                }
                loader(false)
                error(data.error)
            }
        })
    }
    {% endif %}
    {% if not project.has_linked_repo %}
    getElement('link-github-repository').onclick=async()=>{
        {% if request.user.profile.ghID %}
            loader()
            const data = await postRequest2({path:URLS.USER_GH_REPOS,data:{public:true}, retainCache: true});
            
            loader(false)
            if(!data) return
            if(data.code===code.OK){
                let options = '';
                data.repos.forEach((repo)=>{
                    if(!repo.taken)
                        options+=`<option value=${repo.id}>${repo.name}</option>`
                })
                return Swal.fire({
                    title: 'Link GitHub repository',
                    imageUrl: "{% static 'graphics/thirdparty/github.webp' %}",
                    imageWidth:50,
                    html: `<h6>Link GitHub repository to project '{{project.nickname}}'.<br/>Only public repositories can be linked.</h6>
                    <br/>
                    <select class="wide pallete-slab" id="link-github-repository-select">
                        ${options}
                    </select>
                    `,
                    showCancelButton: true,
                    confirmButtonText: 'Link',
                    cancelButtonText: 'Cancel',
                    showLoaderOnConfirm: true,
                    preConfirm: async () => {
                        let repoID = getElement("link-github-repository-select").value
                        if(repoID) return repoID
                        error('Repository required')
                        return false
                    }
                }).then(async (result) => {
                    if (result.isConfirmed) {
                        loader()
                        message("Linking repository...");
                        const data = await postRequest2({
                            path: URLS.LINK_FREE_REPO,
                            data: {
                                projectID,
                                repoID: result.value,
                            }
                        })
                        if(data.code===code.OK){
                            futuremessage("Repository linked.")
                            return window.location.reload()
                        }
                        loader(false)
                        error(data.error)
                    }
                })
            }
            error(data.error)
        {% else %}
            connectWithGithub("{{project.getLink}}", ()=>{ error("Cannot link repository without linking account.")})
        {% endif %}
    }
    {% else %}
    getElement("unlink-github-repository").onclick=_=>{
        Swal.fire({
            title: 'Unlink Github repository?',
            html:`<h6>Are you sure you want to unlink your Github repository '{{project.linked_repo.reponame}}' from your '{{project.nickname}}' project on {{APPNAME}}?</h6>`,
            showCancelButton: true,
            showDenyButton: true,
            showConfirmButton: false,
            denyButtonText: 'Yes, Unlink',
            cancelButtonText: 'No, wait',
        }).then(async(result)=>{
            if(result.isDenied){
                loader()
                message('Unlinking...')
                const data = await postRequest2({path:URLS.UNLINK_FREE_REPO,data:{projectID}})
                if(!data) return loader(false)
                if(data.code===code.OK){
                    futuremessage(`Unlinked your '{{project.linked_repo.reponame}}' repository`)
                    return window.location.reload()
                }
                loader(false)
                error(data.error)
            }
        })
    }
        {% if not project.linked_repo.has_installed_app %}
            Swal.fire({
                title: 'Setup Knottersbot in repository ',
                html:`<h6>To track contribution record in {{project.nickname}} github repository, it is highly recommended that you install our Knotters Bot on GitHub.</h6>`,
                showCancelButton: true,
                showConfirmButton: true,
                confirmButtonText: 'Setup Knotters Bot',
                cancelButtonText: 'Not now',
                allowOutsideClick: false
            }).then(async(result)=>{
                if(result.isConfirmed){
                    miniWindow("https://github.com/apps/knotters-bot/installations/new/permissions?target_id={{request.user.profile.gh_user.id}}")
                }
            })
            
        {% elif project.linked_repo.installed_app.suspended %}
            Swal.fire({
                title: 'Knottersbot suspended',
                html:`<h6>To track contribution record in your {{project.nickname}} github repository, please unsuspend Knotters Bot on GitHub.</h6>`,
                showCancelButton: true,
                showConfirmButton: true,
                confirmButtonText: 'Setup Knotters Bot',
                cancelButtonText: 'Not now',
                allowOutsideClick: false
            }).then(async(result)=>{
                if(result.isConfirmed){
                    miniWindow("https://github.com/apps/knotters-bot/installations/new/permissions?target_id={{request.user.profile.gh_user.id}}")
                }
            })
        {% endif %}
    {% endif %}
    {% if project.can_invite_cocreator %}  
    {% endif %}   
{% else %}
    if(authenticated){
        getElement('report-project').onclick=async()=>{
            await violationReportDialog(URLS.REPORT_PROJECT,{projectID},"{{project.nickname}}", URLS.REPORT_CATEGORIES)   
        }
    }
{% endif %}

{% if iscreator or iscocreator %}
{% endif %}

if(authenticated){
    {% if request.GET.admire == '1' and not isAdmirer %}
        getElement("toggle-admiration").click()
    {% endif %}
    {% if request.GET.admire == '0' and isAdmirer %}
        getElement("toggle-admiration").click()
    {% endif %}
}
getElement('show-admirations').onclick=async(_)=>{
    Swal.fire({ 
        html: await getRequest2({ path:setUrlParams(URLS.ADMIRATIONS, projectID)}), 
        title:"<h4 class='positive-text'>Admirers</h4>"
    })
}
{% if request.GET.admirers %}
getElement('show-admirations').click()
{% endif %}
{% endif %}