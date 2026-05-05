"""
Management command to delete school years from the database.
Usage: 
  - Delete all: python manage.py delete_school_years
  - Delete specific: python manage.py delete_school_years 2027-2028
  - Delete all (no confirmation): python manage.py delete_school_years --force
"""
from django.core.management.base import BaseCommand
from admin_app.models import SchoolYear


class Command(BaseCommand):
    help = 'Delete school years from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            nargs='?',
            type=str,
            help='School year name to delete (e.g., 2027-2028). If not provided, deletes all.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        name = options.get('name')
        force = options.get('force', False)

        if name:
            # Delete specific school year
            try:
                sy = SchoolYear.objects.get(name=name)
                if not force:
                    confirm = input(f'\nAre you sure you want to delete "{name}"? (yes/no): ').strip().lower()
                    if confirm != 'yes':
                        self.stdout.write(self.style.WARNING('Cancelled.'))
                        return

                sy.delete()
                self.stdout.write(self.style.SUCCESS(f'✓ School year "{name}" deleted successfully.'))
            except SchoolYear.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ School year "{name}" not found.'))
        else:
            # Delete all school years
            count = SchoolYear.objects.count()
            if count == 0:
                self.stdout.write(self.style.WARNING('No school years to delete.'))
                return

            if not force:
                confirm = input(f'\nAre you sure you want to delete ALL {count} school year(s)? (yes/no): ').strip().lower()
                if confirm != 'yes':
                    self.stdout.write(self.style.WARNING('Cancelled.'))
                    return

            SchoolYear.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'✓ {count} school year(s) deleted successfully.'))
