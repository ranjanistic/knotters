from faulthandler import disable
from django.core.management.base import BaseCommand
from main.env import ISPRODUCTION,BOTMAIL
from main.methods import errorLog
from main.constants import NotificationCode
from auth2.models import Notification
from projects.models import License, Category
from django.contrib.sites.models import Site
from people.models import Profile, User
from django.conf import settings

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
            'You begin initial setup.'))
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
                'Setting up initial state (does not delete any existing data, intentionally at least)'))
        bot = Profile.KNOTBOT()
        if not bot:
            ubot = User.objects.create_user(email=BOTMAIL,password="1@#2QWqw", first_name="Knotbot")
            bot = Profile.KNOTBOT()
            if not bot:
                bot = Profile.objects.create(user=ubot,nickname="knotboty")
        License.objects.create(name="GNU", keyword="gnuy", description="GNU GPL VN", content="This is a test license, not an original one.", public=True,default=True,creator=bot)
        Category.objects.create(name="Websitey", creator=bot)
        if not Site.objects.filter(id=settings.SITE_ID).exists():
            Site.objects.create(id=settings.SITE_ID, name="Knotters", domain="example.com")
        self.stdout.write(self.style.SUCCESS('Setup done.'))
        self.stdout.write(self.style.SUCCESS('Exiting.'))
        exit(0)

