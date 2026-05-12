from django.core.management.base import BaseCommand
from students_app.utils import resolve_canonical_curriculum_name

class Command(BaseCommand):
    help = 'Normalize mit_curriculum/year values to canonical prospectus names'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Persist changes. Without this flag the command runs as a dry run.',
        )

    def handle(self, *args, **options):
        from students_app.models import EducationalBackground
        from admin_app.models import Application as StudentApplication
        apply_changes = bool(options.get('apply'))

        # Update EducationalBackground
        ebs = EducationalBackground.objects.filter(mit_curriculum__isnull=False).exclude(mit_curriculum__exact='')
        updated_eb = 0
        for eb in ebs:
            val = eb.mit_curriculum.strip()
            canonical = resolve_canonical_curriculum_name(val)
            if canonical and val != canonical:
                self.stdout.write(f'EducationalBackground id={eb.id}: {val} -> {canonical}')
                if apply_changes:
                    eb.mit_curriculum = canonical
                    eb.save(update_fields=['mit_curriculum'])
                updated_eb += 1

        # Update Applications (admin-facing curriculum field)
        updated_app = 0
        apps = StudentApplication.objects.filter(curriculum__isnull=False).exclude(curriculum__exact='')
        for app in apps:
            val = app.curriculum.strip()
            canonical = resolve_canonical_curriculum_name(val)
            if canonical and val != canonical:
                self.stdout.write(f'Application id={app.id}: {val} -> {canonical}')
                if apply_changes:
                    app.curriculum = canonical
                    app.save(update_fields=['curriculum'])
                updated_app += 1

        if apply_changes:
            self.stdout.write(self.style.SUCCESS(
                f'Updated {updated_eb} EducationalBackground rows and {updated_app} Application rows'
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f'Dry run only: {updated_eb} EducationalBackground rows and {updated_app} Application rows would be updated. Re-run with --apply to persist changes.'
            ))
