from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        try:
            picture = sociallogin.account.extra_data['picture']
            user_field(user, "profile_pic", picture)
        except (KeyError, AttributeError):
            pass
        return user