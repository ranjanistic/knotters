if ("{{request.GET.e}}") error("{{request.GET.e}}");
if ("{{request.GET.a}}") message("{{request.GET.a}}");
if ("{{request.GET.s}}") success("{{request.GET.s}}");
if ("{{request.GET.report}}" === "1") reportFeedbackView();
if ("{{request.GET.contact}}" === "1") contactRequestDialog();
if ("{{request.GET.formerr}}") error("{{request.GET.formerr}}");
if ("{{request.GET.msg}}") message("{{request.GET.msg}}");
if ("{{request.GET.menu}}" == "1") openMenu(); 
