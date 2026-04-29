"""
Management command to check existing student data in the database.
Usage: python manage.py check_student_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from students_app.models import PersonalDetails, Document, PrivacyConsent
from admin_app.models import Application


class Command(BaseCommand):
    help = 'Check existing student data in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== STUDENT DATA SUMMARY ===\n'))

        # Count users
        total_users = User.objects.count()
        non_superusers = User.objects.filter(is_superuser=False).count()
        superusers = User.objects.filter(is_superuser=True).count()

        self.stdout.write(f'Total Users: {total_users}')
        self.stdout.write(f'  - Regular Users: {non_superusers}')
        self.stdout.write(f'  - Superusers: {superusers}\n')

        # Count personal details
        personal_details = PersonalDetails.objects.count()
        self.stdout.write(f'Personal Details Records: {personal_details}')

        # Count documents
        documents = Document.objects.count()
        self.stdout.write(f'Documents Uploaded: {documents}')

        # Count applications
        applications = Application.objects.count()
        self.stdout.write(f'Applications Created: {applications}\n')

        # Count privacy consents
        privacy_consents = PrivacyConsent.objects.filter(agreed=True).count()
        self.stdout.write(
            f'Submitted Applications (Privacy Consent): {privacy_consents}\n')

        # List actual student data
        if non_superusers > 0:
            self.stdout.write(self.style.SUCCESS('=== STUDENT USERS ===\n'))
            students = User.objects.filter(is_superuser=False)
            for idx, student in enumerate(students, 1):
                self.stdout.write(
                    f'{idx}. {student.username} ({student.email})')

                # Check personal details
                try:
                    personal = PersonalDetails.objects.get(user=student)
                    self.stdout.write(
                        f'   ✓ Personal Details: {personal.first_name} {personal.last_name}')
                except PersonalDetails.DoesNotExist:
                    self.stdout.write(f'   ✗ Personal Details: None')

                # Check documents
                docs = Document.objects.filter(user=student)
                self.stdout.write(f'   Documents: {docs.count()}')
                for doc in docs:
                    doc_type = doc.get_document_type_display()
                    self.stdout.write(f'     - {doc_type}')

                # Check application
                try:
                    app = Application.objects.get(user=student)
                    self.stdout.write(
                        f'   ✓ Application: {app.application_id} ({app.status})')
                except Application.DoesNotExist:
                    self.stdout.write(f'   ✗ Application: Not created yet')

                # Check privacy consent
                try:
                    consent = PrivacyConsent.objects.get(
                        user=student, agreed=True)
                    self.stdout.write(f'   ✓ Submitted: Yes')
                except PrivacyConsent.DoesNotExist:
                    self.stdout.write(f'   ✗ Submitted: No')

                self.stdout.write('')

        # Recommendation
        if applications == 0 and personal_details > 0:
            self.stdout.write(self.style.WARNING('\n⚠️  RECOMMENDATION:'))
            self.stdout.write(
                'Students have filled forms but no Application records exist.')
            self.stdout.write('You need to:')
            self.stdout.write('  1. Run migrations: python manage.py migrate')
            self.stdout.write(
                '  2. Create Application records for existing students')
            self.stdout.write(
                '  3. Or run: python manage.py initialize_admin_data\n')
        elif applications > 0:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ All set! Application records exist in database.'))
            self.stdout.write(
                'You can access the admin dashboard without running initialize_admin_data.\n')
