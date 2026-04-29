from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from students_app.models import (
    UserProfile, PersonalDetails, EducationalBackground,
    WorkingStudent, PrivacyConsent, Document
)


class Command(BaseCommand):
    help = 'Delete all records related to a user by email address'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Email address of the user whose records should be deleted'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete without confirmation'
        )

    def handle(self, *args, **options):
        email = options['email']
        force = options['force']

        # Find the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email "{email}" not found.')
            )
            return

        # Display what will be deleted
        self.stdout.write(self.style.WARNING(
            f'\nDeleting records for user: {email}'))
        self.stdout.write(f'Username: {user.username}')
        self.stdout.write(f'User ID: {user.id}')

        # Count records that will be deleted
        personal_count = PersonalDetails.objects.filter(user=user).count()
        education_count = EducationalBackground.objects.filter(
            user=user).count()
        working_count = WorkingStudent.objects.filter(user=user).count()
        privacy_count = PrivacyConsent.objects.filter(user=user).count()
        document_count = Document.objects.filter(user=user).count()
        profile_count = UserProfile.objects.filter(user=user).count()

        self.stdout.write('\nRecords to be deleted:')
        self.stdout.write(f'  - Personal Details: {personal_count}')
        self.stdout.write(f'  - Educational Background: {education_count}')
        self.stdout.write(f'  - Working Student: {working_count}')
        self.stdout.write(f'  - Privacy Consent: {privacy_count}')
        self.stdout.write(f'  - Documents: {document_count}')
        self.stdout.write(f'  - User Profile: {profile_count}')
        self.stdout.write(f'  - User Account: 1')

        # Confirm before deleting
        if not force:
            confirm = input(
                '\nAre you sure you want to delete all these records? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion cancelled.'))
                return

        # Delete all related records
        try:
            # Delete in proper order (respecting foreign keys)
            Document.objects.filter(user=user).delete()
            PrivacyConsent.objects.filter(user=user).delete()
            WorkingStudent.objects.filter(user=user).delete()
            EducationalBackground.objects.filter(user=user).delete()
            PersonalDetails.objects.filter(user=user).delete()
            UserProfile.objects.filter(user=user).delete()

            # Finally delete the user account
            username = user.username
            user.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Successfully deleted all records for user "{email}"')
            )
            self.stdout.write(self.style.SUCCESS(
                f'✓ User account "{username}" has been deleted'))
            self.stdout.write(self.style.SUCCESS(
                '\nThe user can now create a new account and restart their application.'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'\n✗ Error occurred during deletion: {str(e)}')
            )
