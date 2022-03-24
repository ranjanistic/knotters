{% if request.GET.next != URLS.ROOT and request.GET.next %}
  message("Please login to continue")
{% endif %}