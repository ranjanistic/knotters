{% load static %}
{% load i18n %}
{% load l10n %}
{% load tz %}
{% load cache %}
{% load custom_tags %}

const projectID = "{{ project.getID }}";
const selfProject = "{{iscreator}}"==='True';
const ismoderator = "{{ismoderator}}"==='True';
const projectcolor = getComputedStyle(document.querySelector(':root')).getPropertyValue('--accent').trim().replace('#','');

{% if not project.suspended %}
if(!selfProject){
    if(authenticated){
        getElement('report-project').onclick=async()=>{
            await violationReportDialog(URLS.REPORT_PROJECT,{projectID},"{{project.nickname}}", URLS.REPORT_CATEGORIES)   
        }
    }
}

{% if iscreator or ismoderator %}
   
        getElement('save-edit-projecttags').onclick= async ()=> {
            var obj = getFormDataById("edit-tag-inputs");
            var resp=await postRequest2({path:setUrlParams(URLS.TAGSUPDATE, projectID), data:{
                addtagIDs:obj.addtagIDs.split(',').filter((str)=>str),addtags:obj.addtags.split(',').filter((str)=>str),removetagIDs:obj.removetagIDs.split(',').filter((str)=>str)
            }, retainCache: true});
            console.log(resp)
            if (resp.code===code.OK){
                subLoader()
                return window.location.reload()
            }
            error(resp.error)
        }
        getElement('sociallinks-add').onclick=_=>{
            const parent=getElement('edit-sociallinks-inputs');
            if(parent.childElementCount===5) return message('Maximun URLs limit reached')
            const linkNumber=parent.childElementCount+1;
            const newChild=document.createElement('div');
            newChild.innerHTML = `
                <input class="wide" type="url" inputmode="url" placeholder="Link to anything relevant" name="sociallink${linkNumber}" id=sociallink${linkNumber} /><br/><br/>
            `;
            parent.insertBefore(newChild,parent.childNodes[0]);
        }
    
    {% if iscreator and project.can_invite_owner %}
    
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
                    },
                    retainCache: true
                })
                if(data.code===code.OK){
                    futuremessage("Invitation sent.")
                    return window.location.reload()
                }
                error(data.error)
            }
        })
    }
    {% elif iscreator and project.under_invitation %}
        getElement('delete-project-invitation').onclick=async(e)=>{
            message("Deleting invitation...");
            const data = await postRequest2({
                path: URLS.INVITE_PROJECT_OWNER,
                data: {
                    action: 'remove',
                    projectID,
                },
                retainCache: true
            })
            if(data.code===code.OK){
                futuremessage("Invitation cancelled")
                return window.location.reload()
            }
            error(data.error)
        }
    {% endif %}
    
    {% if not project.under_mod_invitation and ismoderator %}
    
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
                    path: URLS.INVITE_VERPROJECT_MOD,
                    data: {
                        action: 'create',
                        projectID,
                        email: result.value,
                    },
                    retainCache: true
                })
                if(data.code===code.OK){
                    futuremessage("Invitation sent.")
                    return window.location.reload()
                }
                error(data.error)
            }
        })
    }
    {% elif ismoderator %}
        getElement('delete-project-mod-invitation').onclick=async(e)=>{
            message("Deleting moderation invitation...");
            const data = await postRequest2({
                path: URLS.INVITE_VERPROJECT_MOD,
                data: {
                    action: 'remove',
                    projectID,
                },
                retainCache: true
            })
            if(data.code===code.OK){
                futuremessage("Moderation Invitation cancelled")
                return window.location.reload()
            }
            error(data.error)
        }
    {% endif %}
    {% if iscreator and project.under_del_request %}
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
    {% elif iscreator and project.can_request_deletion %}
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