from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0024_rename_program_code_to_program_label'),
    ]

    operations = [
        migrations.AddField(
            model_name='adminprofile',
            name='preferences',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Admin UI preferences: academic_year, default_program, etc.',
            ),
        ),
    ]
