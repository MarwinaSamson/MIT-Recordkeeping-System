# Generated migration for adding downloads field to CMSSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0007_remove_cmssettings_announcement_text_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cmssettings',
            name='downloads',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='List of downloadable files: [{name, url, file_type}]'
            ),
        ),
    ]
