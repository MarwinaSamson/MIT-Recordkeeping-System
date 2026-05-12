from django.db import migrations


def update_mit_program_label(apps, schema_editor):
    Program = apps.get_model('admin_app', 'Program')
    Program.objects.filter(name='MIT').update(program_label="Master's Degree")


def restore_mit_program_code(apps, schema_editor):
    Program = apps.get_model('admin_app', 'Program')
    Program.objects.filter(name='MIT').update(program_label='MIT')


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0023_seed_program_levels'),
    ]

    operations = [
        migrations.RenameField(
            model_name='program',
            old_name='code',
            new_name='program_label',
        ),
        migrations.RunPython(update_mit_program_label, restore_mit_program_code),
    ]