from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .env import ISPRODUCTION, PUBNAME, SITE
from .strings import url
from people.models import Profile


def sendEmail(to: str, subject: str, html: str, body: str) -> bool:
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=[to])
            msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except:
            return False
    else:
        print(to, body)
        return True


def sendCCEmail(to: list, subject: str, html: str, body: str) -> bool:
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=to)
            msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except:
            return False
    else:
        print(to, body)
        return True


def getEmailHtmlBody(greeting: str, header: str, footer: str, actions: list = [], conclusion: str = '') -> str and str:
    """
    Creates html and body content using parameters via the application's standard email template.

    :greeting: Top greeting to target
    :header: Beginnning text
    :footer: Ending text
    :actions: Actions, list of { text, url } to be included in content
    :conclusion: Final short summary text

    :returns: html, body
    """
    data = {
        'greeting': greeting,
        'headertext': header,
        'footertext': footer,
        'current_site': {
            'name': PUBNAME,
            'domain': SITE
        }
    }
    body = f"{greeting}\n\n{header}\n\n"

    updatedActions = []
    for act in actions:
        if str(act.url).__contains__(SITE):
            updatedActions.append(act)
        elif str(act.url).startswith('http'):
            updatedActions.append({
                'text': act.text,
                'url': f"{SITE}/{url.REDIRECTOR}?n={act.url}"
            })
        else:
            updatedActions.append({
                'text': act.text,
                'url': f"{SITE}{'' if str(act.url).startswith('/') else '/'}{act.url}"
            })

    if len(updatedActions):
        data['actions'] = updatedActions
        for action in updatedActions:
            body = f"{body}{action['url']}\n"

    if conclusion:
        data['conclusion'] = conclusion
        body = f"{body}\n{footer}\n{conclusion}"

    try:
        html = render_to_string('account/email/email.html', data)
        return html, body
    except:
        return '', body


def sendAlertEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str, greeting: str = '') -> bool:
    greeting = greeting if greeting else f"Hello {username}"
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendCCAlertEmail(to: list, subject: str, header: str, footer: str, conclusion: str, greeting: str = 'Hello') -> bool:
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendActionEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str = '', actions: list = [], greeting: str = '') -> bool:
    """

    :actions: List of { text:str, url: str }
    """
    greeting = greeting if greeting else f"Hello {username}"
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion, actions=actions)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendCCActionEmail(to: list, subject: str, header: str, footer: str, conclusion: str = '', actions: list = [], greeting: str = 'Hello') -> bool:
    """

    :actions: List of { text:str, url: str }
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion, actions=actions)
    return sendCCEmail(to=to, subject=subject, html=html, body=body)


def downtimeAlert() -> list:
    """
    To alert all users about any downtime, meant for manual invokation via shell.
    """
    
    tillTime = str(input("Downtime Till (Month DD, YYYY, HH:MM): ")) + " (IST Asia/Kolkata)"
    print(tillTime)
    profiles = Profile.objects.filter(is_zombie=False,to_be_zombie=False)
    mails = []
    for prof in profiles:
        sendAlertEmail(
            to=prof.getEmail(),
            username=prof.getFName(),
            subject="Scheduled Downtime Alert",
            header=f"This is to inform you that our online platform will experience a downtime till {tillTime}, due to unavoidable changes for the good.",
            footer="Any inconvenience is deeply regretted. Thank you for your understanding.",
            conclusion="You received this alert because you are a member of our community. If this is an error, the please report to us."
        )
        mails.append({
            'to': prof.getEmail(),
            'username': prof.getFName()
        })
    print("Downtime alerted"),
    return mails