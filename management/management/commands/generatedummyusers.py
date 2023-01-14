from django.core.management.base import BaseCommand
from main.env import ISPRODUCTION
from main.methods import createDummyUsers


class Command(BaseCommand):

    help = """
        To generate the dummy users.
        NOTE: Do not use this command if you are not sure what you are doing.
        """

    def add_arguments(self, parser):
        parser.add_argument('--noinput', action='store_true',
                            help='accepts no prompts from the command line.', default=False)
        parser.add_argument('--limit', type=int , help='provide number of dummy users to be generated.', default=5)

    def handle(self, *args, **options):
        limit = options['limit']
        self.stdout.write(self.style.WARNING(
            f'You are about to generate {limit} dummy user(s).'))
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
                'Generating dummy users...'))
        done = createDummyUsers(limit)
        if done:
            self.stdout.write(self.style.SUCCESS(
                f'{limit} Dummy users generated.'))
            self.stdout.write(self.style.SUCCESS('Done.'))
        else:
            self.stdout.write(self.style.ERROR(
                'Failed to generate dummy users'))
        self.stdout.write(self.style.SUCCESS('Exiting.'))
        exit(0)

