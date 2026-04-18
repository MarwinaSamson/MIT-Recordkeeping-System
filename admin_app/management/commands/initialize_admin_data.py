"""
Management command to initialize admin dashboard with sample data.
Usage: python manage.py initialize_admin_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from admin_app.models import Application, DocumentVerification, AdminActivityLog
from students_app.models import Document, PersonalDetails


class Command(BaseCommand):
    help = 'Initialize admin dashboard with sample applications and documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete all existing test data before creating new data',
        )

    def handle(self, *args, **options):
        if options['delete']:
            self.stdout.write('Deleting existing test data...')
            Application.objects.filter(application_id__startswith='TEST-').delete()
            self.stdout.write(self.style.SUCCESS('Test data deleted'))

        self.stdout.write('Creating sample data...')
        
        # Get or create superuser for testing
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@wmsu.edu.ph',
                'is_superuser': True,
                'is_staff': True,
                'first_name': 'Admin',
                'last_name': 'User',
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {admin_user.username}'))
        
        # Sample data
        samples = [
            {
                'username': 'student1',
                'email': 'student1@example.com',
                'first_name': 'Noellene Pearl',
                'last_name': 'Villarcampo',
                'application_id': 'MIT-0001',
                'program': 'MIT',
                'status': 'reviewing',
                'mobile': '+639610056461',
            },
            {
                'username': 'student2',
                'email': 'student2@example.com',
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'application_id': 'MIT-0002',
                'program': 'MIT',
                'status': 'verified',
                'mobile': '+639171234567',
            },
            {
                'username': 'student3',
                'email': 'student3@example.com',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'application_id': 'MIT-0003',
                'program': 'MBA',
                'status': 'pending',
                'mobile': '+639189876543',
            },
            {
                'username': 'student4',
                'email': 'student4@example.com',
                'first_name': 'Pedro',
                'last_name': 'Reyes',
                'application_id': 'MIT-0004',
                'program': 'MPA',
                'status': 'incomplete',
                'mobile': '+639201112222',
            },
        ]
        
        created_count = 0
        for sample in samples:
            user, created = User.objects.get_or_create(
                username=sample['username'],
                defaults={
                    'email': sample['email'],
                    'first_name': sample['first_name'],
                    'last_name': sample['last_name'],
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
            
            # Create personal details if not exist
            PersonalDetails.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': sample['first_name'],
                    'last_name': sample['last_name'],
                    'dob': '1990-01-01',
                    'gender': 'Female',
                    'civil_status': 'Single',
                    'place_of_birth': 'Zamboanga City',
                    'religion': 'Catholic',
                    'ethnicity': 'Chavacano',
                    'nationality': 'Filipino',
                    'disability': 'None',
                    'permanent_address': '123 Sample St., Zamboanga City',
                    'contact_number': sample['mobile'],
                    'email': sample['email'],
                    'name_of_parent': 'Parent Name',
                    'relationship': 'Parent',
                    'parent_income': '50,000 - 100,000',
                }
            )
            
            # Create application
            Application.objects.get_or_create(
                application_id=sample['application_id'],
                defaults={
                    'user': user,
                    'program': sample['program'],
                    'status': sample['status'],
                    'remarks': f'Sample application for {sample["first_name"]} {sample["last_name"]}',
                }
            )
            
            # Create sample documents
            doc_types = ['tor', 'deans_recommendation', 'psa']
            for doc_type in doc_types:
                doc, doc_created = Document.objects.get_or_create(
                    user=user,
                    document_type=doc_type,
                    defaults={
                        'file_name': f'{doc_type}_sample.pdf',
                        'file': 'documents/sample.pdf',
                    }
                )
                
                # Create document verification
                if sample['status'] == 'verified':
                    doc_status = 'verified'
                    verified_by = admin_user
                    verified_at = timezone.now()
                elif sample['status'] == 'reviewing':
                    doc_status = 'reviewing'
                    verified_by = None
                    verified_at = None
                elif sample['status'] == 'incomplete':
                    doc_status = 'pending'
                    verified_by = None
                    verified_at = None
                else:
                    doc_status = 'pending'
                    verified_by = None
                    verified_at = None
                
                DocumentVerification.objects.get_or_create(
                    document=doc,
                    defaults={
                        'status': doc_status,
                        'verified_by': verified_by,
                        'verified_at': verified_at,
                        'remarks': f'{doc_type} sample document',
                    }
                )
            
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} sample students'))
        self.stdout.write(self.style.SUCCESS('Admin dashboard data initialized successfully!'))
        self.stdout.write(self.style.WARNING('Test credentials:'))
        self.stdout.write(f'  Username: admin')
        self.stdout.write(f'  Password: admin123')
