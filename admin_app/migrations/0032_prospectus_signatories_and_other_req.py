from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0031_prospectus_extra_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='prospectus',
            name='prepared_by_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='prepared_by_title',
            field=models.CharField(blank=True, default='MIT Department Curriculum Committee Chair', max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='prepared_by_date',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='noted_by_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='noted_by_title',
            field=models.CharField(blank=True, default='College Dean', max_length=255),
        ),
        migrations.AddField(
            model_name='prospectus',
            name='noted_by_date',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='prospectussemester',
            name='is_other_req',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='prospectussubject',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
