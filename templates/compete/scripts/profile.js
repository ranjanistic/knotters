const compID = "{{compete.getID}}";
const isActive = "{{compete.isActive}}" == "True";
const resultDeclared = "{{compete.resultDeclared}}" == "True";
const tabindex = Number("{{request.GET.tab}}") || false;
if (tabindex) {
    window.location.href = "#mainframe";
}
{% if compete.isActive %}
const userFreeProjectsSelect = (done = (_) => {}) => {
    Swal.fire({
        title: "Select your quick project to submit",
        html: `
         <h6>Please make sure that your chosen project has a linked source code repository, 
         and its commits should not predate this competition's duration. 
         Your quick project should be created within the duration of this competition only.<br/>
         <br/>
        <a href="{{URLS.Projects.CREATE_FREE}}" target="_blank">Click here to create a new Quick project</a> for this competition.</h6>
        The following list will only show your Quick projects that are created after {{compete.startAt}}
        <br/>Refresh this page to see the updated list.
        <select class="pallete-slab wide" id="selected-quick-project">
         <option value="">Click to choose</option>
         {% for proj in request.user.profile.free_projects %}
         {% if proj.createdOn >= compete.startAt %}
          <option value="{{proj.get_id}}">{{proj.name}} ({{proj.nickname}}) </option>
          {% endif %}
         {% endfor %}
        </select>
         This will override any previously saved submission for this competition.
         <span class="negative-text" id="error-qp"></span>
      `,
        preConfirm: () => {
            const selectedID = getElement(
                "selected-quick-project"
            ).value.trim();
            if (!selectedID) {
                getElement("error-qp").innerHTML =
                    "Please select a project from list";
                return false;
            }
            return selectedID;
        },
        showConfirmButton: true,
        confirmButtonText: "Set as submission",
        showCancelButton: true,
    }).then((result) => {
        if (result.isConfirmed) {
            return done(result.value);
        }
        return done(false);
    });
};
{% endif %}
