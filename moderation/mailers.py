from people.models import Profile
from main.strings import CORE_PROJECT, PROJECTS, COMPETE, PEOPLE
from main.mailers import sendActionEmail, sendAlertEmail
from main.env import PUBNAME
from .models import Moderation


def moderationAssignedAlert(moderation: Moderation) -> bool:
    return sendActionEmail(
        to=moderation.moderator.getEmail(),
        username=moderation.moderator.getName(),
        subject="New Moderation Assigned",
        header=f"A new {['project', 'competition', 'person', 'core project'][[PROJECTS, COMPETE, PEOPLE, CORE_PROJECT].index(moderation.type)]} moderation has been assigned to you to review. The following link button will take you directly to the moderation view.",
        actions=[{
            'text': 'View moderation',
            'url': moderation.getLink()
        }],
        footer=f"Take action only after thoroughly reviewing this moderation. This moderation will become stale in {moderation.stale_days} days if not responded.",
        conclusion=f"You received this email because you're a moderator at {PUBNAME}. If this is an error, please report to us."
    )


def moderationActionAlert(moderation: Moderation, status: str) -> bool:
    return sendAlertEmail(
        to=moderation.moderator.getEmail(),
        username=moderation.moderator.getFName(),
        subject=f"Moderation {status.capitalize()}",
        header=f"This is to inform you that a {['project', 'competition', 'person', 'core project'][[PROJECTS, COMPETE, PEOPLE, CORE_PROJECT].index(moderation.type)]} moderation has been {status} by you as the assigned moderator.",
        actions=[{
            'text': 'View moderation',
            'url': moderation.getLink()
        }],
        footer="If you acknowledge this action, then this email can be ignored safely.",
        conclusion=f"You received this email because you're a moderator at {PUBNAME}. If this is an error, please report to us."
    )

def madeModeratorAlert(profile: Profile) -> bool:
    return sendActionEmail(
        to=profile.getEmail(),
        username=profile.getFName(),
        subject=f"Promotion to Moderator",
        header=f"Congratulations! You have been made one of our moderators. This brings previleges and duties with rewards! The following link button will brief you as a moderator.",
        actions=[{
            'text':"Get started",
            'url': '/docs/moderationguidelines'
        }],
        footer=f"It's fun and rewarding to be a moderator at {PUBNAME}, and we wish you loads of luck with your adventure lying ahead!",
        conclusion=f"You received this email because you've been made a moderator at {PUBNAME}. You can always withdraw from this previlege via your account settings."
    )
