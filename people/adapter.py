from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        try:
            if str(sociallogin.account.provider).lower() == 'discord':
                picture = f"https://cdn.discordapp.com/avatars/{sociallogin.account.uid}/{sociallogin.account.extra_data['avatar']}.png?size=1024"
            elif str(sociallogin.account.provider).lower() == 'github':
                picture = sociallogin.account.extra_data['avatar_url']
            elif str(sociallogin.account.provider).lower() == 'google':
                link = str(sociallogin.account.extra_data['picture'])
                linkpart = link.split("=")[0]
                sizesplit = link.split("=")[1].split("-")
                sizesplit.remove(sizesplit[0])
                picture = "=".join([linkpart, "-".join(["s512", "-".join(sizesplit)])])
            else: return user
            user_field(user, "profile_pic", picture)
        except (KeyError, AttributeError):
            pass
        return user
    