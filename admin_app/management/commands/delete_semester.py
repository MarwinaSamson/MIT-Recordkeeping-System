from django.core.management.base import BaseCommand
from admin_app.models import Semester

class Command(BaseCommand):
    help = 'Delete a semester by ID'

    def add_arguments(self, parser):
        parser.add_argument('semester_id', type=int, help='Semester ID to delete')

    def handle(self, *args, **options):
        semester_id = options['semester_id']
        try:
            semester = Semester.objects.get(id=semester_id)
            semester_name = str(semester)
            semester.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted: {semester_name}'))
        except Semester.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Semester with ID {semester_id} not found'))