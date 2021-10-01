from django.core.mail.message import EmailMessage, sanitize_address
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, send_mass_mail
from people.models import Profile
from django.conf import settings
from .methods import errorLog, addMethodToAsyncQueue
from .env import ISDEVELOPMENT, ISPRODUCTION, PUBNAME, SITE
from .strings import URL
from django.core.mail.backends.smtp import EmailBackend as EB
import smtplib


class EmailBackend(EB):

    def queue_send_mail(connection,from_email, recipients, message, fail_silently):
        try:
            connection.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
        except smtplib.SMTPException:
            if not fail_silently:
                raise
            return False
        return True

    def _send(self, email_message):
        """Override of the default helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.message()
        addMethodToAsyncQueue(f"main.mailers.{EmailBackend.__name__}.{EmailBackend.queue_send_mail.__name__}",self.connection,from_email, recipients, message.as_bytes(linesep='\r\n'),self.fail_silently)
        return True
        


def sendEmail(to: str, subject: str, html: str, body: str) -> bool:
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=[to])
            msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except Exception as e:
            errorLog(e)
            return False
    else:
        if ISDEVELOPMENT:
            print(to)
            print(subject)
            print(body)
        return True


def sendCCEmail(to: list, subject: str, html: str, body: str) -> bool:
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=to)
            msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except Exception as e:
            errorLog(e)
            return False
    else:
        if ISDEVELOPMENT:
            print(to)
            print(subject)
            print(body)
        return True

def sendBulkEmails(emails:list,subject,html,body):
    for email in emails:
        sendEmail(email,subject,html,body)
    return True

def getEmailHtmlBody(header: str, footer: str, username: str = '', actions: list = [],greeting: str = '', conclusion: str = '', action=False) -> str and str:
    """
    Creates html and body content using parameters via the application's standard email template.

    :greeting: Top greeting to target
    :header: Beginnning text
    :footer: Ending text
    :actions: Actions, list of { text, url } to be included in content
    :conclusion: Final short summary text
    :action: Final short summary text

    :returns: html, body
    """
    data = {
        'greeting': greeting,
        'username': username,
        'headertext': header,
        'footertext': footer,
        'current_site': {
            'name': PUBNAME,
            'domain': SITE
        }
    }
    body = f"{greeting}\n\n{header}\n\n"

    if action:
        updatedActions = []

        for act in actions:
            acttext = act['text']
            acturl = act['url']
            if str(acturl).__contains__(SITE):
                updatedActions.append(act)
            elif str(acturl).startswith('http'):
                updatedActions.append({
                    'text': acttext,
                    'url': f"{SITE}/{URL.REDIRECTOR}?n={acturl}"
                })
            else:
                updatedActions.append({
                    'text': acttext,
                    'url': f"{SITE}{'' if str(acturl).startswith('/') else '/'}{acturl}"
                })

        if len(updatedActions):
            data['actions'] = updatedActions
            for action in updatedActions:
                body = f"{body}{action['url']}\n"

    if conclusion:
        data['conclusion'] = conclusion
        body = f"{body}\n{footer}\n{conclusion}"

    try:
        html = render_to_string(
            f"account/email/{'action' if action else 'alert'}.html", data)
        return html, body
    except Exception as e:
        errorLog(e)
        return '', body


def sendAlertEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str = '', greeting: str = '') -> bool:
    html, body = getEmailHtmlBody(
        greeting=greeting, username=username, header=header, footer=footer, conclusion=conclusion)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendCCAlertEmail(to: list, subject: str, header: str, footer: str, conclusion: str = '', greeting: str = 'Hello') -> bool:
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendActionEmail(to: str, subject: str, header: str, footer: str, conclusion: str = '', actions: list = [], username: str = '', greeting: str = '') -> bool:
    """

    :actions: List of { text:str, url: str }
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, username=username, header=header, footer=footer, conclusion=conclusion, actions=actions, action=True)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendCCActionEmail(to: list, subject: str, header: str, footer: str, conclusion: str = '', actions: list = [], greeting: str = 'Hello') -> bool:
    """

    :actions: List of { text:str, url: str }
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion, actions=actions, action=True)
    return sendCCEmail(to=to, subject=subject, html=html, body=body)


def featureRelease(name,content):
    emails = Profile.objects.filter(is_active=True,suspended=False,to_be_zombie=False).values_list("user__email",flat=True)
    html, body = getEmailHtmlBody(header=f'A new feature release - {name} - of {PUBNAME} is here! This release has the following details.', footer=content, conclusion="You aren't required to take any action. You were notified because you are a member. You can stop receiving such emails in future.")
    return sendBulkEmails(emails,'Feature Release!',html, body)

def downtimeAlert():
    """
    To alert all users about any downtime, meant for manual invokation via shell only.
    """

    tillTime = str(input("Downtime Till (Month DD, YYYY, HH:MM): ")).strip()
    print(tillTime)
    emails = Profile.objects.filter(is_zombie=False).values_list('user__email',flat=True)
    if(input(f"{emails.count()} people will be alerted, ok? (y/n) ")!='y'):
        return print("aborted.")
    print('Alert task started.')
    
    html, body = getEmailHtmlBody(
        greeting='', 
        header=f"This is to inform you that our online platform will experience a downtime till {tillTime}, due to unavoidable reasons.", 
        footer="Any inconvenience is deeply regretted. Thank you for your understanding.", 
        conclusion="You received this alert because you are a member of our community. If this is an error, then please report to us."
    )
    addMethodToAsyncQueue(f'main.mailers.{sendBulkEmails.__name__}', emails,"Scheduled Downtime Alert",html,body)
