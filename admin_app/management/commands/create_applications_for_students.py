"""
Management command to create Application records for existing students.
Usage: python manage.py create_applications_for_students
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from students_app.models import PersonalDetails, PrivacyConsent
from admin_app.models import Application


class Command(BaseCommand):
    help = 'Create Application records for existing students who have submitted forms'

    def handle(self, *args, **options):
        self.stdout.write(
            'Creating Application records for existing students...\n')

        # Get all non-superuser students
        students = User.objects.filter(is_superuser=False)

        if not students.exists():
            self.stdout.write(self.style.WARNING(
                'No student users found in database.'))
            return

        created_count = 0
        skipped_count = 0

        for student in students:
            # Check if application already exists
            if Application.objects.filter(user=student).exists():
                skipped_count += 1
                self.stdout.write(
                    f'⊘ {student.email}: Application already exists')
                continue

            # Get personal details to determine program (default to MIT)
            program = 'MIT'
            try:
                personal = PersonalDetails.objects.get(user=student)
                # You can add logic here to determine program based on personal details
            except PersonalDetails.DoesNotExist:
                pass

            # Check if student has submitted (privacy consent agreed)
            try:
                consent = PrivacyConsent.objects.get(user=student, agreed=True)
                status = 'pending'  # Default status
            except PrivacyConsent.DoesNotExist:
                status = 'incomplete'  # Not yet submitted

            # Generate application ID
            # Format: PROGRAM-XXXX (e.g., MIT-0001)
            count = Application.objects.filter(program=program).count() + 1
            application_id = f'{program}-{count:04d}'

            # Create application
            Application.objects.create(
                user=student,
                program=program,
                application_id=application_id,
                status=status,
                remarks=f'Application for {student.email}'
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(
                f'✓ {student.email}: Created {application_id} ({status})'))

        self.stdout.write(
            f'\n{self.style.SUCCESS("Created: " + str(created_count))}')
        self.stdout.write(
            f'{self.style.WARNING("Skipped: " + str(skipped_count))}')

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Application records created successfully!'))
            self.stdout.write(
                'You can now access the admin dashboard to view and manage applications.')
