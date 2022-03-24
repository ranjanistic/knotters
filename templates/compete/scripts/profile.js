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
         and its commits should not predate this competition's duration. You can also <a href="{{URLS.Projects.CREATE_FREE}}" target="_blank">create a new Quick project</a> for this competition as well.</h6>
        <select class="pallete-slab wide" id="selected-quick-project">
         <option value="">Click to choose</option>
         {% for proj in request.user.profile.free_projects %}
          <option value="{{proj.get_id}}">{{proj.name}} ({{proj.nickname}})</option>
         {% endfor %}
        </select>
         This will override any saved submission URL for this competition.
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
