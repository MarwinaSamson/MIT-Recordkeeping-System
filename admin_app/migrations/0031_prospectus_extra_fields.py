from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0030_add_is_core_is_specialization_to_subject'),
    ]

    operations = [
        migrations.AddField(
            model_name='prospectus',
            name='college',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='full_program_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='cmo_ref',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='bor_ref',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='effective_year',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]
