{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

const projectID = "{{ project.get_id }}";
const selfProject = "{{iscreator}}"==='True';
const ismoderator = "{{ismoderator}}" === 'True';
const iscreator = selfProject;
const iscocreator = "{{iscocreator}}"==='True';
const isSuspended = "{{project.suspended}}"==='True';
const projectcolor = getComputedStyle(document.querySelector(':root')).getPropertyValue('--{{project.theme}}').trim().replace('#','');
const isRater = "{{isRater}}"==='True';

{% if not project.suspended %}
    {% if iscreator %}
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
        {% if project.under_del_request %}
            getElement('cancel-delete-project-request').onclick=async(e)=>{
                message("Cancelling deletion request...");
                const data = await postRequest2({
                    path: setUrlParams(URLS.TRASH, projectID),
                    data: {
                        action: 'remove',
                        projectID,
                    },
                    retainCache: true
                })
                if(data.code===code.OK){
                    futuremessage("Deletion request cancelled.")
                    return window.location.reload()
                }
                error(data.error)
            }
        {% elif project.can_request_deletion %}
            getElement('delete-project-request').onclick=async(e)=>{
                Swal.fire({
                    title: 'Request project deletion',
                    html: `<h6>Are you sure you want to request permanent deletion of '{{project.nickname}}' project?<br/>
                    The request will be sent to the moderator to decide.</h6>
                    `,
                    showCancelButton: true,
                    showConfirmButton: false,
                    cancelButtonText: 'No, go back',
                    showDenyButton: true,
                    denyButtonText: 'Yes, request deletion',
                    preConfirm: async () => {
                    
                    }
                }).then(async (result) => {
                    if (result.isDenied) {
                        message("Requesting project deletion...");
                        const data = await postRequest2({
                            path: setUrlParams(URLS.TRASH, projectID),
                            data: {
                                action: 'create',
                                projectID,
                            },
                            retainCache: true
                        })
                        if(data.code===code.OK){
                            futuremessage("Deletion request sent.")
                            return window.location.reload()
                        }
                        error(data.error)
                        
                    }
                });
            }
        {% endif %}
        {% if project.can_request_verification %}
        getElement('request-verification').onclick=async(e)=>{
            const ldata = await getRequest2({path:URLS.PUB_LICENSES});
            if(!ldata||ldata.code!=CODE.OK) return error(ldata.error);
            const licenses = ldata.licenses.map(l=>`<option value="${l.id}">${l.name}</option>`).join('');
            Swal.fire({
                title: 'Request verification',
                html: `
                    <strong>
                    By requesting verification, you are submitting your project for review by the current moderator.
                    If approved, your project will no longer exist as Core project, and the linked source code will be made publicly visible,
                    and your project will become a verified project on Knotters.</strong>
                    <br/><br/>
                    Choose a license<br/>
                    <select class="pallete-slab positive-text wide" id="verification-license">
                        ${licenses}
                    </select>
                    <br/>
                    Project detail for moderator to read<br/>
                    <textarea class="wide" placeholder="Reason for verification" id="request-verification-reason"></textarea>
                    <br/>
                    Maximum days to review<br/>
                    <input type="number" class="wide" min="1" max="15" placeholder="Stale days (min 1, max 15)" value="3" id="request-verification-stale-days" />
                    <br/>
                `,
                showCancelButton: true,
                confirmButtonText: 'Send Request',
                cancelButtonText: 'Cancel',
                preConfirm: async () => {
                    const licenseID = getElement('verification-license').value.trim()
                    if(!licenseID){
                        error('License required');
                        return false;
                    }
                    const reason = getElement('request-verification-reason').value.trim()
                    if(!reason){
                        error('Reason required')
                        return false;
                    }
                    const stale_days = getElement('request-verification-stale-days').value
                    if(!stale_days){
                        error('Stale days required')
                        return false;
                    }
                    return {
                        reason,
                        stale_days:Number(stale_days), 
                        licenseID
                    }
                }
            }).then(async(result)=>{
                if(result.isConfirmed){
                    loader()
                    message("Sending request...");
                    const data = await postRequest2({
                        path: setUrlParams(URLS.CORE_VERIFICATION_REQUEST),
                        data: {
                            action: 'create',
                            projectID,
                            requestData: result.value.reason,
                            stale_days:result.value.stale_days,
                            licenseID:result.value.licenseID,
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
                    then cancellation will not be possible, and this core project may already have been deleted.</strong>
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
                        path: setUrlParams(URLS.CORE_VERIFICATION_REQUEST),
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
    {% elif ismoderator %}
        {% if not project.under_mod_invitation %}
        getElement('transfer-project-mod').onclick=(e)=>{
            Swal.fire({
                title: 'Transfer project moderatorship',
                html: `<h6>Transfer project '{{project.nickname}}' to another moderator.<br/>
                Invite the new moderator by their email to transfer moderation.</h6>
                <br/>
                <input class="wide" type="email" autocomplete="email" placeholder="New email address" id="transfer-project-mod-new-email" />
                `,
                showCancelButton: true,
                confirmButtonText: 'Send Invite',
                cancelButtonText: 'Cancel',
                showLoaderOnConfirm: true,
                preConfirm: async () => {
                    let email = getElement("transfer-project-mod-new-email").value.trim()
                    if(email) return email
                    error('Email address required')
                    return false
                }
            }).then(async (result) => {
                if (result.isConfirmed) {
                    message("Sending moderator invitation...");
                    const data = await postRequest2({
                        path: URLS.INVITE_COREPROJECT_MOD,
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
        {% else %}
            getElement('delete-project-mod-invitation').onclick=async(e)=>{
                message("Deleting moderation invitation...");
                const data = await postRequest2({
                    path: URLS.INVITE_COREPROJECT_MOD,
                    data: {
                        action: 'remove',
                        projectID,
                    }
                })
                if(data.code===code.OK){
                    futuremessage("Moderation Invitation cancelled")
                    return window.location.reload()
                }
                error(data.error)
            }
        {% endif %}
    {% endif %}
    {% if request.GET.admirers %}
    getElement('show-admirations').click()
    {% endif %}
    {% if request.user.is_authenticated %}
        {% if request.GET.admire == '1' and not isAdmirer %}
            getElement("toggle-admiration").click()
        {% endif %}
        {% if request.GET.admire == '0' and isAdmirer %}
            getElement("toggle-admiration").click()
        {% endif %}
    {% endif %}
{% endif %}