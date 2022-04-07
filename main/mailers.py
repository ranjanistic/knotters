from smtplib import SMTPException

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend as EB
from django.core.mail.message import sanitize_address
from django.template.loader import render_to_string
from management.models import ThirdPartyAccount
from people.models import Profile

from .env import ISDEVELOPMENT, ISPRODUCTION, PUBNAME, SERVER_EMAIL, SITE
from .methods import addMethodToAsyncQueue, errorLog, htmlmin
from .strings import URL


class EmailBackend(EB):

    def queue_send_mail(connection, from_email, recipients, message, fail_silently):
        try:
            connection.sendmail(from_email, recipients,
                                message.as_bytes(linesep='\r\n'))
        except SMTPException as s:
            if not fail_silently:
                errorLog(s)
            return False
        except Exception as e:
            errorLog(e)
            return False
        return True

    def _send(self, email_message):
        """Override of the default helper method that does the actual sending."""
        if not email_message.recipients():
            return False
        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)
        recipients = [sanitize_address(addr, encoding)
                      for addr in email_message.recipients()]
        message = email_message.message()
        addMethodToAsyncQueue(f"main.mailers.{EmailBackend.__name__}.{EmailBackend.queue_send_mail.__name__}",
                              self.connection, from_email, recipients, message.as_bytes(linesep='\r\n'), self.fail_silently)
        return True


def sendEmail(to: str, subject: str, html: str, body: str) -> bool:
    """To send email to a single recipient.

    Args:
        to (str): Recipient's email address
        subject (str): Email subject
        html (str, optional): Email html content
        body (str): Email body content

    Returns:
        bool: True if email was sent successfully, False otherwise

    NOTE: In development mode, the email is sent to the console.
    """
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=[to])
            if html:
                msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except Exception as e:
            errorLog(e)
            return False
    else:
        if ISDEVELOPMENT:
            print("\n==============EMAIL==============")
            print("TO:", to)
            print("SUBJECT:", subject)
            print("BODY:", body)
            print("==============END EMAIL==============\n")
        return True


def sendCCEmail(to: list, subject: str, html: str, body: str) -> bool:
    """To send email to multiple recipients as CC.

    Args:
        to (list<str>): List of recipients' email addresses
        subject (str): Email subject
        html (str, optional): Email html content
        body (str): Email body content

    Returns:
        bool: True if email was sent successfully, False otherwise

    NOTE: In development mode, the email is sent to the console.
    """
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=to)
            if html:
                msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except Exception as e:
            errorLog(e)
            return False
    else:
        if ISDEVELOPMENT:
            print("\n==============CC EMAIL==============")
            print("CC:", to)
            print("SUBJECT:", subject)
            print("BODY:", body)
            print("==============END CC EMAIL==============\n")
        return True


def sendBulkEmails(emails: list, subject: str, html: str, body: str) -> list:
    """To send email to multiple recipients, separetly with same subject and content.

    Args:
        emails (list<str>): List of recipients' email addresses
        subject (str): Email subject
        html (str): Email html content
        body (str): Email body content

    Returns:
        list<bool>: List of True with corresponding email addresses if email was sent successfully, False otherwise.

    NOTE: In development mode, the emails are sent to the console.
    """
    if ISDEVELOPMENT:
        print("\n==============BULK EMAILS==============")
        print("TO:", emails)
        print("SUBJECT:", subject)
        print("BODY:", body)
        print("==============END BULK EMAILS==============\n")
        return [[True, email] for email in emails]
    else:
        donelist = []
        for email in emails:
            done = sendEmail(email, subject, html, body)
            donelist.append([email, done])
    return donelist


def getEmailHtmlBody(header: str, footer: str, username: str = '', actions: list = [], greeting: str = '', conclusion: str = '', action=False) -> str and str:
    """Creates html and body content using parameters via the application's standard email template depending upon action.

    Args:
        header (str): Email header content
        footer (str): Email footer content
        username (str, optional): Username of the user
        actions (list<str>, optional): List of actions to be displayed in the email
        greeting (str, optional): Greeting to be displayed in the email
        conclusion (str, optional): Conclusion to be displayed in the email
        action (bool, optional): If email template type is action, or an alert.

    Returns:
        str, str: Email html content, Email body content
    """
    data = dict(
        greeting=greeting,
        username=username,
        headertext=header,
        footertext=footer,
        current_site=dict(
            name=PUBNAME,
            domain=SITE
        ),
        SOCIALS=ThirdPartyAccount.get_all()
    )

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
        html = htmlmin(render_to_string(
            f"account/email/{'action' if action else 'alert'}.html", data))
        return html, body
    except Exception as e:
        errorLog(e)
        return '', body


def sendAlertEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str = '', greeting: str = '') -> str:
    """To queue task to send alert type email to a single recipient.

    Args:
        to (str): Recipient's email address
        username (str): Display name of the user
        subject (str): Email subject
        header (str): Email header content
        footer (str): Email footer content
        conclusion (str, optional): Email conclusion
        greeting (str, optional): Email greeting. If not provided, default is 'Hello there,'

    Returns:
        str: The task ID
        bool: False if task not queued
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, username=username, header=header, footer=footer, conclusion=conclusion)
    return addMethodToAsyncQueue(f"main.mailers.{sendEmail.__name__}", to, subject, html, body)


def sendCCAlertEmail(to: list, subject: str, header: str, footer: str, conclusion: str = '', greeting: str = 'Hello') -> bool:
    """To queue task to send alert type email to multiple recipients as CC.

    Args:
        to (list<str>): List of recipients' email addresses
        subject (str): Email subject
        header (str): Email header content
        footer (str): Email footer content
        conclusion (str, optional): Email conclusion.
        greeting (str, optional): Email greeting. If not provided, default is 'Hello'

    Returns:
        str: The task ID
        bool: False if task not queued
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion)
    return addMethodToAsyncQueue(f"main.mailers.{sendCCEmail.__name__}", to, subject, html, body)


def sendActionEmail(to: str, subject: str, header: str, footer: str, conclusion: str = '', actions: list = [], username: str = '', greeting: str = '') -> bool:
    """To queue task to send action type email to a single recipient.

    Args:
        to (str): Recipient's email address
        subject (str): Email subject
        header (str): Email header content
        footer (str): Email footer content
        conclusion (str, optional): Email conclusion
        actions (list<dict>, optional): List of actions to be displayed in the email. Default is empty list. Following is the format of each action:
            {
                'text': 'Action text',
                'url': 'Action url'
            }
        username (str, optional): Display name of the user
        greeting (str, optional): Email greeting. If not provided, default is 'Hello there,'

    Returns:
        str: The task ID
        bool: False if task not queued
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, username=username, header=header, footer=footer, conclusion=conclusion, actions=actions, action=True)
    return addMethodToAsyncQueue(f"main.mailers.{sendEmail.__name__}", to, subject, html, body)


def sendCCActionEmail(to: list, subject: str, header: str, footer: str, conclusion: str = '', actions: list = [], greeting: str = 'Hello') -> bool:
    """To queue task to send action type email to multiple recipients as CC.

    Args:
        to (list<str>): List of recipients' email addresses
        subject (str): Email subject
        header (str): Email header content
        footer (str): Email footer content
        conclusion (str, optional): Email conclusion
        actions (list, optional): List of actions to be displayed in the email. Default is empty list. Following is the format of each action:
            {
                'text': 'Action text',
                'url': 'Action url'
            }
        greeting (str, optional): Email greeting. If not provided, default is 'Hello'

    Returns:
        str: The task ID
        bool: False if task not queued
    """
    html, body = getEmailHtmlBody(
        greeting=greeting, header=header, footer=footer, conclusion=conclusion, actions=actions, action=True)
    return addMethodToAsyncQueue(f"main.mailers.{sendCCEmail.__name__}", to, subject, html, body)


def featureRelease(name, content):
    emails = Profile.objects.filter(
        is_active=True, suspended=False, to_be_zombie=False).values_list("user__email", flat=True)
    html, body = getEmailHtmlBody(header=f'A new feature release - {name} - of {PUBNAME} is here! This release has the following details.', footer=content,
                                  conclusion="You aren't required to take any action. You were notified because you are a member. You can stop receiving such emails in future.")
    return addMethodToAsyncQueue(f"main.mailers.{sendBulkEmails.__name__}", emails, 'Feature Release!', html, body)


def downtimeAlert():
    """
    To alert all users about any downtime, meant for manual invokation via shell only.

    Returns:
        str: The task ID
        bool: False if task not queued
    """

    tillTime = str(input("Downtime Till (Month DD, YYYY, HH:MM): ")).strip()
    print(tillTime)
    emails = Profile.objects.filter(
        is_zombie=False).values_list('user__email', flat=True)
    if(input(f"{emails.count()} people will be alerted, ok? (y/n) ") != 'y'):
        return print("aborted.")
    print('Alert task started.')

    html, body = getEmailHtmlBody(
        greeting='',
        header=f"This is to inform you that our online platform will experience a downtime till {tillTime}, due to unavoidable reasons.",
        footer="Any inconvenience is deeply regretted. Thank you for your understanding.",
        conclusion="You received this alert because you are a member of our community. If this is an error, then please report to us."
    )
    addMethodToAsyncQueue(f'main.mailers.{sendBulkEmails.__name__}', emails, "Scheduled Downtime Alert", html, body)

def sendToAdmin(subject:str, body:str, html:str) -> str:
    """To send email to admin.

    Args:
        head (str): Email Heading
        body (str): Email body
        html (str): Email html

    Returns:
        str: The task ID
        bool: False if task not queued
    """
    return addMethodToAsyncQueue(f"main.mailers.{sendEmail.__name__}", SERVER_EMAIL, subject, html, body)

def sendErrorLog(error: Exception) -> bool:
    """To send error log to admin.

    Args:
        error (Exception): Error object, str

    Returns:
        str: The task ID
        bool: False if task not queued
    """
    return sendToAdmin(f"KnottersERROR LOG", error, error)

