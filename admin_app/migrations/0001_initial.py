# Generated migration for admin_app models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('students_app', '0003_add_current_session_key_to_userprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('program', models.CharField(choices=[('MIT', 'Master of Information Technology'), (
                    'MBA', 'Master of Business Administration'), ('MPA', 'Master of Public Administration')], default='MIT', max_length=50)),
                ('application_id', models.CharField(max_length=50, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('reviewing', 'Under Review'), (
                    'verified', 'Verified'), ('incomplete', 'Incomplete'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('submission_date', models.DateTimeField(auto_now_add=True)),
                ('last_activity', models.DateTimeField(auto_now=True)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                 related_name='application', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-submission_date'],
            },
        ),
        migrations.CreateModel(
            name='DocumentVerification',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'Pending Review'), ('reviewing', 'Under Review'), (
                    'verified', 'Verified'), ('incomplete', 'Incomplete'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('rejection_reason', models.TextField(blank=True)),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('document', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                 related_name='verification', to='students_app.document')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                 related_name='verified_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='AdminActivityLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('verified', 'Verified Document'), ('rejected', 'Rejected Document'), ('incomplete', 'Marked Incomplete'), (
                    'resubmit', 'Requested Resubmission'), ('note', 'Added Note'), ('comment', 'Added Comment')], max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                 related_name='admin_activities', to=settings.AUTH_USER_MODEL)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                 related_name='activity_logs', to='admin_app.application')),
                ('document', models.ForeignKey(blank=True, null=True,
                 on_delete=django.db.models.deletion.SET_NULL, to='students_app.document')),
            ],
            options={
                'verbose_name': 'Admin Activity Log',
                'verbose_name_plural': 'Admin Activity Logs',
                'ordering': ['-timestamp'],
            },
        ),
    ]
