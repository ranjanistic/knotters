from main.env import PUBNAME
from main.mailers import sendActionEmail
from main.strings import URL

from .models import User


def welcomeAlert(user: User) -> str:
    """
    Send an email to a new user with a welcome message.
    """
    return sendActionEmail(
        to=user.email,
        username=user.getName(),
        greeting='Welcome',
        subject=f"Welcome to {PUBNAME} Community",
        header="We're pleased to let you know that you're now a part of our booming community! This comes with lot of opportunities "
        "to create, learn and contribute towards the betterment of everyone.",
        actions=[dict(
            text='Get started',
            url=f"/{URL.HOME}"
        )],
        footer="Please do not hesitate if you have any doubts or queries to ask. Do checkout our social channels (links below) for direct interactions.",
        conclusion=f"This email was sent because you created an account on {PUBNAME}. If there's a problem, then please report to us."
    )
