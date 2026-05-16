from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0012_alter_gradeentry_options_gradeentry_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='gradeentry',
            name='admin_verified',
            field=models.BooleanField(default=False),
        ),
    ]
