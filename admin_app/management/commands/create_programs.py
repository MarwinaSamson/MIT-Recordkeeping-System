from django.core.management.base import BaseCommand

from admin_app.models import Program


class Command(BaseCommand):
    help = 'Create initial Program records (e.g., MIT)'

    def handle(self, *args, **options):
        created = []
        name = 'MIT'
        p, ok = Program.objects.get_or_create(name=name, defaults={'code': 'MIT', 'description': 'Master of Information Technology'})
        if ok:
            created.append(p.name)
            self.stdout.write(self.style.SUCCESS(f'Created program: {p.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Program already exists: {p.name}'))

        if created:
            self.stdout.write(self.style.SUCCESS('Programs creation complete.'))
        else:
            self.stdout.write('No new programs created.')
