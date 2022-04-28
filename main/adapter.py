from urllib.parse import urlencode

from allauth_2fa.adapter import OTPAdapter

from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse

class CustomOTPAdapter(OTPAdapter):
    """
    Custom OTP adapter as the default allauth_2fa adapter does not work correctly with latest allauth version.
    """
    def login(self, request, user):
        if self.has_2fa_enabled(user):
            request.session["allauth_2fa_user_id"] = str(user.id)
            redirect_url = reverse("two-factor-authenticate")
            print("here")
            query_params = request.GET.copy()
            try:
                view = request.resolver_match.func.view_class()
                view.request = request
                success_url = view.get_success_url()
                if success_url:
                    query_params[view.redirect_field_name] = success_url
            except: pass
            if query_params:
                redirect_url += "?" + urlencode(query_params)

            raise ImmediateHttpResponse(response=HttpResponseRedirect(redirect_url))

        return super().login(request, user)
