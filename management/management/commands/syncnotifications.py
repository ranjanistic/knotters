from faulthandler import disable
from django.core.management.base import BaseCommand
from main.env import ISPRODUCTION
from main.methods import errorLog
from main.constants import NotificationCode
from auth2.models import Notification


class Command(BaseCommand):

    help = """
        To generate the notifications based on the latest templates.
        This command can be used when existing notifications are to be updated with latest changes in design.
        NOTE: Do not use this command if you are not sure what you are doing.
        NOTE: Trying to stop the execution of this command may result in loss of notifications.
        Pass --please parameter to actually start the command.
        """

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true',
                            help='accepts no prompts from the command line.', default=False)
        pass

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'You are about to generate new notifications and update existing notifications.'))
        if ISPRODUCTION:
            self.stdout.write(self.style.WARNING(
                '\nPRODUCTION ENVIRONMENT DETECTED.\n'))
        if not options.get('noinput', False):
            self.stdout.write(self.style.WARNING(
                'Are you sure you want to proceed? (y/N)'))
            answer = input()
            if answer.lower() != 'y':
                self.stdout.write(self.style.ERROR('Aborting.'))
                return exit(0)
            self.stdout.write(self.style.WARNING(
                'Synchronising notifications...'))

        done = synchroniseNotifications()
        if done:
            self.stdout.write(self.style.SUCCESS(
                'Notifications Synchronised.'))
            self.stdout.write(self.style.SUCCESS('Done.'))
        else:
            self.stdout.write(self.style.ERROR(
                'Notifications synchronisation error.'))
        self.stdout.write(self.style.SUCCESS('Exiting.'))
        exit(0)


def synchroniseNotifications():
    try:
        notifs = NotificationCode().getDetails()
        newnotifications = []
        countcreate = 0
        countupdate = 0
        for notif in notifs:

            if not Notification.objects.filter(code=notif["code"]).exists():
                newnotifications.append(Notification(
                    name=notif["name"], description=notif["description"], code=notif["code"], disabled=notif.get("disabled", False)))
            else:
                Notification.objects.filter(
                    code=notif["code"]).update(name=notif["name"], description=notif["description"], code=notif["code"], disabled=notif.get("disabled", False))
                countupdate += 1

        countcreate = Notification.objects.bulk_create(newnotifications)
        codes = list(map(lambda notif: notif["code"], notifs))
        count, _ = Notification.objects.exclude(code__in=codes).delete()
        print(f"\n{len(countcreate)} notifications created.")
        print(f"\n{countupdate} notifications updated.")
        print(f"\n{count} notifications deleted.")
        return True
    except Exception as e:
        errorLog(e)
        return False
