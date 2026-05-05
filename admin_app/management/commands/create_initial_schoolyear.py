"""
Management command to create initial school year data for testing.
Usage: python manage.py create_initial_schoolyear
"""
from django.core.management.base import BaseCommand
from admin_app.models import SchoolYear


class Command(BaseCommand):
    help = 'Create an initial active school year for testing'

    def handle(self, *args, **options):
        # Check if any school year exists
        if SchoolYear.objects.exists():
            self.stdout.write(self.style.WARNING('School years already exist in database.'))
            self.stdout.write('Current school years:')
            for sy in SchoolYear.objects.all():
                status = '✓ ACTIVE' if sy.is_active else '○ INACTIVE'
                self.stdout.write(f'  - {sy.name} ({status})')
            return

        # Create initial school year
        sy = SchoolYear.objects.create(
            name='2027-2028',
            status='enrollment-open',
            is_active=True,
            notes='Initial school year for testing'
        )

        self.stdout.write(self.style.SUCCESS(f'✓ Created active school year: {sy.name}'))
        self.stdout.write(self.style.SUCCESS('You can now see the banner and school year data in the admin panel.'))
