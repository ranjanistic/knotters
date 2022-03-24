{% if request.GET.next != URLS.ROOT and request.GET.next %}
  message("Please signup to continue")
{% endif %}