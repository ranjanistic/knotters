from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .env import ISPRODUCTION


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


def getEmailHtmlBody(greeting: str, header: str, footer: str, actions: list = [], conclusion: str = '') -> str and str:
    """
    Creates html and body content using parameters via the application's standard email template.

    :greeting: Top greeting to target
    :header: Beginnning text
    :footer: Ending text
    :actions: Actions { name, url } to be included in content
    :conclusion: Final short summary text

    :returns: html, body
    """
    data = {
        'greeting': greeting,
        'headertext': header,
        'footertext': footer,
        'current_site': {
            'name': 'Knotters',
            'domain': 'knotters.org'
        }
    }
    body = f"{greeting}\n\n{header}\n\n"
    if actions:
        data['actions'] = actions
        for action in actions:
            body = f"{body}{action['url']}\n"

    if conclusion:
        data['conclusion'] = conclusion
        body = f"{body}\n{conclusion}"

    html = render_to_string('account/email/email.html', data)
    return html, body


def sendAlertEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str) -> bool:
    html, body = getEmailHtmlBody(
        greeting=f"Hello {username}", header=header, footer=footer, conclusion=conclusion)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendActionEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str = '', actions: list = []) -> bool:
    html, body = getEmailHtmlBody(
        greeting=f"Hello {username}", header=header, footer=footer, conclusion=conclusion, actions=actions)
    return sendEmail(to=to, subject=subject, html=html, body=body)
