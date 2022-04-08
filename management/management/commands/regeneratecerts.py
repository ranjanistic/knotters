from compete.methods import (generateJudgeCertificate, generateModCertificate,
                             generateParticipantCertificate)
from compete.models import AppreciationCertificate, ParticipantCertificate
from django.core.management.base import BaseCommand
from django_q.tasks import async_task
from main.env import ISPRODUCTION
from main.methods import errorLog
from management.apps import APPNAME


class Command(BaseCommand):

    help = """
        To regenerate the certificates based on the latest templates, depends on MEDIA_ROOT setting.
        This command can be used when existing certificates are to be updated with latest changes in design.
        This WILL NOT notify the users about the changes, and will work with the certificate files and their stored records in database only, and only for active users.
        None of the paths & IDs of any certificate will change, and the certificate records will remain the same after successful regeneration.
        NOTE: Do not use this command if you are not sure what you are doing.
        NOTE: Trying to stop the execution of this command may result in loss of certificates.
        Pass --please parameter to actually start the command.
        """

    def add_arguments(self, parser):
        parser.add_argument('--please', action='store_true',
                            help='To actually start the command.', default=False)
        parser.add_argument('--qcluster', action='store_true',
                            help='Run the generation in qcluster (background).', default=False)
        pass

    def handle(self, *args, **options):
        if not options.get('please', False):
            self.stdout.write(self.style.ERROR(
                'You have not read the instructions carefully. Please read the instructions by passing --help parameter.'))
            return exit(0)

        self.stdout.write(self.style.WARNING(
            'You are about to regenerate all the existing certificates.'))
        self.stdout.write(self.style.WARNING(
            'This is a bulk action, involving potential risks of loss of certificates, if used incorrectly.'))
        if ISPRODUCTION:
            self.stdout.write(self.style.WARNING('\n⚠💀 PRODUCTION ENVIRONMENT DETECTED. PROCEED WITH CAUTION 💀⚠\n'))
        self.stdout.write(self.style.WARNING(
            'Are you sure you want to proceed? (y/N)'))
        answer = input()
        if answer.lower() != 'y':
            self.stdout.write(self.style.ERROR('Aborting.'))
            return exit(0)

        self.stdout.write(self.style.WARNING('Generating certificates...'))
        if options['qcluster']:
            taskID = async_task(
                f"{APPNAME}.management.commands.regeneratecerts.{startRegenerationOfAllCertificates.__name__}")
            self.stdout.write(self.style.SUCCESS(
                f'Track by task ID: {taskID}'))
            exit(0)
        else:
            self.stdout.write(self.style.WARNING(
                '💀 DO NOT close the terminal window or try to kill this process while the command is running to avoid loss of certificates 💀\n'))
            done = startRegenerationOfAllCertificates()
            if done:
                self.stdout.write(self.style.SUCCESS(
                    'Certificates regenerated.'))
                self.stdout.write(self.style.SUCCESS('Done.'))
            else:
                self.stdout.write(self.style.ERROR(
                    'Certificates regeneration error.'))
            self.stdout.write(self.style.SUCCESS('Exiting.'))
        exit(0)


def startRegenerationOfAllCertificates():
    try:
        print("\nStarting regeneration of all certificates according to stored certificate records.\n")
        print("\nRegenerating certificates for appreciants...")
        appcertificates = AppreciationCertificate.objects.exclude(
            certificate="").exclude(certificate=None)
        for appcertificate in appcertificates:
            if appcertificate.appreciatee.is_normal:
                print(
                    f"Generating certificate for {appcertificate.competition} {appcertificate.appreciatee}...")
                if appcertificate.competition.isJudge(appcertificate.appreciatee):
                    crt = generateJudgeCertificate(
                        appcertificate.appreciatee, appcertificate.competition, appcertificate.id.hex)
                else:
                    crt = generateModCertificate(
                        appcertificate.competition, appcertificate.id.hex)
                if crt:
                    print("done", crt)
                else:
                    errorLog("cert regeneration error", appcertificate, crt)

        print("\nRegenerating certificates for participants...")
        partcertificates = ParticipantCertificate.objects.exclude(
            certificate="").exclude(certificate=None)
        for partcertificate in partcertificates:
            if partcertificate.profile.is_normal:
                print(
                    f"Generating certificate for {partcertificate.profile} {partcertificate.result}...")
                crt = generateParticipantCertificate(
                    partcertificate.profile, partcertificate.result, partcertificate.id.hex)
                if crt:
                    print("done", crt)
                else:
                    errorLog("cert regeneration error", partcertificates, crt)
        print("\nDone.")
        return True
    except Exception as e:
        errorLog(e)
        return False
