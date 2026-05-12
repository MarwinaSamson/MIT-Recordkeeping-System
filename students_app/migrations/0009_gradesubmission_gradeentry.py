from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('students_app', '0008_alter_document_document_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='GradeSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curriculum_name', models.CharField(blank=True, max_length=255)),
                ('school_year', models.CharField(blank=True, max_length=32)),
                ('semester', models.CharField(blank=True, max_length=64)),
                ('gpa', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('screenshot', models.FileField(blank=True, null=True, upload_to='grade_submissions/')),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Acknowledged', 'Acknowledged'), ('Flagged', 'Flagged')], default='Pending', max_length=20)),
                ('admin_remarks', models.TextField(blank=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grade_submissions', to='auth.user')),
            ],
            options={
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='GradeEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year_label', models.CharField(blank=True, max_length=120)),
                ('semester_label', models.CharField(blank=True, max_length=120)),
                ('code', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=512)),
                ('units', models.PositiveSmallIntegerField(default=0)),
                ('grade', models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True)),
                ('remarks', models.CharField(blank=True, max_length=255)),
                ('order', models.PositiveIntegerField(default=0)),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='students_app.gradesubmission')),
            ],
            options={
                'ordering': ['order'],
                'unique_together': {('submission', 'year_label', 'semester_label', 'code')},
            },
        ),
    ]
