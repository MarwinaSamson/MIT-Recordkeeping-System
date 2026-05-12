from django.db import migrations


def seed_program_levels(apps, schema_editor):
    Program = apps.get_model('admin_app', 'Program')
    defaults = [
        ('masters', "Master's Degree", "Graduate program level used for master's applications."),
        ('doctoral', 'Doctoral Degree', 'Graduate program level used for doctoral applications.'),
        ('certificate', 'Certificate Program', 'Certificate-level program option.'),
    ]

    for name, code, description in defaults:
        Program.objects.update_or_create(
            name=name,
            defaults={
                'code': code,
                'description': description,
            },
        )


def unseed_program_levels(apps, schema_editor):
    Program = apps.get_model('admin_app', 'Program')
    Program.objects.filter(name__in=['masters', 'doctoral', 'certificate']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0022_semester'),
    ]

    operations = [
        migrations.RunPython(seed_program_levels, unseed_program_levels),
    ]