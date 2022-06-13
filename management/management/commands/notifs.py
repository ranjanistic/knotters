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
        parser.add_argument('--please', action='store_true',
                            help='To actually start the command.', default=False)
        pass

    def handle(self, *args, **options):
        if not options.get('please', False):
            self.stdout.write(self.style.ERROR(
                'You have not read the instructions carefully. Please read the instructions by passing --help parameter.'))
            return exit(0)

        self.stdout.write(self.style.WARNING(
            'You are about to generate new notifications and update existing notifications.'))
        if ISPRODUCTION:
            self.stdout.write(self.style.WARNING(
                '\n⚠💀 PRODUCTION ENVIRONMENT DETECTED. PROCEED WITH CAUTION 💀⚠\n'))
        self.stdout.write(self.style.WARNING(
            'Are you sure you want to proceed? (y/N)'))
        answer = input()
        if answer.lower() != 'y':
            self.stdout.write(self.style.ERROR('Aborting.'))
            return exit(0)

        self.stdout.write(self.style.WARNING('Generating notifications...'))

        self.stdout.write(self.style.WARNING(
            '💀 DO NOT close the terminal window or try to kill this process while the command is running to avoid loss of notifications 💀\n'))
        done = generateNotif()
        if done:
            self.stdout.write(self.style.SUCCESS(
                'Notifications generated and updated.'))
            self.stdout.write(self.style.SUCCESS('Done.'))
        else:
            self.stdout.write(self.style.ERROR(
                'Notifications generation error.'))
        self.stdout.write(self.style.SUCCESS('Exiting.'))
        exit(0)


def generateNotif():
    try:
        name = NotificationCode.names
        length = len(name)
        description = NotificationCode.description
        for i in range(1,length+1):
            if not Notification.objects.filter(code=i).exists():
                Notification.objects.create(
                    name=name[i-1], description=description[i-1], code=i)
            else:
                Notification.objects.filter(code=i).update(
                    name=name[i-1], description=description[i-1])
        Notification.objects.filter(code__gte=length+1).delete()
        print("\nDone.")
        return True
    except Exception as e:
        errorLog(e)
        return False
