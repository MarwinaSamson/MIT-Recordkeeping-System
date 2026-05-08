from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Migrate mit_curriculum/year values to prospectus names where possible'

    def handle(self, *args, **options):
        from admin_app.models import ProspectusAssignment
        from students_app.models import EducationalBackground
        from ..models import Application as StudentApplication
        # Build mapping intake_year -> prospectus.name
        mapping = {}
        assignments = ProspectusAssignment.objects.select_related('prospectus').all()
        for a in assignments:
            if getattr(a, 'prospectus', None) and a.intake_year:
                name = (a.prospectus.name or '').strip()
                if name:
                    mapping[a.intake_year.strip()] = name

        if not mapping:
            self.stdout.write('No prospectus assignments with intake_year found. Nothing to do.')
            return

        self.stdout.write(f'Found {len(mapping)} intake->name mappings')

        # Update EducationalBackground
        ebs = EducationalBackground.objects.filter(mit_curriculum__isnull=False).exclude(mit_curriculum__exact='')
        updated_eb = 0
        for eb in ebs:
            val = eb.mit_curriculum.strip()
            if val in mapping and val != mapping[val]:
                self.stdout.write(f'Updating EducationalBackground id={eb.id}: {val} -> {mapping[val]}')
                eb.mit_curriculum = mapping[val]
                eb.save()
                updated_eb += 1

        # Update Applications (admin-facing curriculum field)
        updated_app = 0
        apps = StudentApplication.objects.filter(curriculum__isnull=False).exclude(curriculum__exact='')
        for app in apps:
            val = app.curriculum.strip()
            if val in mapping and val != mapping[val]:
                self.stdout.write(f'Updating Application id={app.id}: {val} -> {mapping[val]}')
                app.curriculum = mapping[val]
                app.save()
                updated_app += 1

        self.stdout.write(self.style.SUCCESS(f'Updated {updated_eb} EducationalBackground rows and {updated_app} Application rows'))
