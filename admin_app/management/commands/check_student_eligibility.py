"""
Management command to inspect why a student is or is not eligible for enrollment.

Usage:
    python manage.py check_student_eligibility <identifier>
    python manage.py check_student_eligibility <identifier> --field username
    python manage.py check_student_eligibility --all

Identifier can be matched against:
    - user id
    - username
    - email
    - application_id
"""

from decimal import Decimal
import re

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from admin_app.models import Application, CMSSettings, DocumentVerification
from students_app.models import CORSubmission, Document, GradeEntry, GradeSubmission, PersonalDetails


def _title_to_key(title):
    if not title:
        return ''
    return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')


class Command(BaseCommand):
    help = 'Show why a student is or is not eligible for enrollment'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            nargs='?',
            help='Student identifier: user id, username, email, or application ID',
        )
        parser.add_argument(
            '--field',
            choices=['auto', 'id', 'username', 'email', 'application_id'],
            default='auto',
            help='How to interpret the identifier (default: auto-detect)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Print eligibility status for all students with applications',
        )

    def handle(self, *args, **options):
        if options['all']:
            self.print_all_students()
            return

        identifier = options.get('identifier')
        if not identifier:
            raise CommandError('Provide an identifier or use --all.')

        user = self.resolve_user(identifier, options['field'])
        if not user:
            raise CommandError(f'No student found for identifier: {identifier}')

        self.print_student_status(user)

    def resolve_user(self, identifier, field='auto'):
        if field in ('auto', 'id'):
            try:
                return User.objects.get(id=int(identifier))
            except (ValueError, User.DoesNotExist):
                if field == 'id':
                    return None

        if field in ('auto', 'username'):
            user = User.objects.filter(username__iexact=identifier).first()
            if user:
                return user

        if field in ('auto', 'email'):
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user

        if field in ('auto', 'application_id'):
            app = Application.objects.select_related('user').filter(
                application_id__iexact=identifier
            ).first()
            if app:
                return app.user

        return None

    def print_all_students(self):
        users = User.objects.filter(application__isnull=False).select_related('application').order_by('username')
        self.stdout.write(self.style.SUCCESS('=== STUDENT ELIGIBILITY SUMMARY ===\n'))
        for user in users:
            summary = self.build_status(user)
            status_label = 'ELIGIBLE' if summary['is_eligible'] else 'NOT ELIGIBLE'
            self.stdout.write(f"{user.username} ({summary['student_id']}): {status_label}")
            if summary['eligibility_reasons']:
                for reason in summary['eligibility_reasons']:
                    self.stdout.write(f"  - {reason}")
            self.stdout.write('')

    def print_student_status(self, user):
        summary = self.build_status(user)
        self.stdout.write(self.style.SUCCESS('=== STUDENT ELIGIBILITY CHECK ===\n'))
        self.stdout.write(f"Name: {summary['full_name']}")
        self.stdout.write(f"Username: {user.username}")
        self.stdout.write(f"Email: {user.email}")
        self.stdout.write(f"Application ID: {summary['student_id']}")
        self.stdout.write(f"Eligible: {'YES' if summary['is_eligible'] else 'NO'}\n")

        self.stdout.write('Documents:')
        self.stdout.write(f"  Uploaded verified docs: {summary['documents_uploaded']} / {summary['documents_required']}")
        if summary['missing_documents']:
            self.stdout.write('  Missing documents:')
            for doc in summary['missing_documents']:
                self.stdout.write(f'    - {doc}')
        else:
            self.stdout.write('  Missing documents: none')

        self.stdout.write(f"COR verified: {'YES' if summary['cor_uploaded'] else 'NO'}")

        self.stdout.write('Grades:')
        self.stdout.write(f"  Failing grades: {summary['failing_grades']}")
        if summary['failing_subjects']:
            self.stdout.write('  Failing subjects:')
            for subject in summary['failing_subjects']:
                self.stdout.write(f'    - {subject}')
        else:
            self.stdout.write('  Failing subjects: none')

        self.stdout.write(f"  GWA: {summary['gwa'] if summary['gwa'] is not None else 'N/A'}")

        self.stdout.write('\nCMS requirements:')
        if summary['required_items']:
            for item in summary['required_items']:
                status = 'VERIFIED' if item['key'] in summary['verified_titles'] else ('UPLOADED, NOT VERIFIED' if item['key'] in summary['uploaded_titles'] else 'MISSING')
                self.stdout.write(f"  - {item['title']} [{status}]")
        else:
            self.stdout.write('  - No CMS admission requirements configured')

        self.stdout.write('\nUploaded document titles:')
        if summary['uploaded_titles']:
            for title in sorted(summary['uploaded_titles']):
                self.stdout.write(f'  - {title}')
        else:
            self.stdout.write('  - none')

        self.stdout.write('\nVerified document titles:')
        if summary['verified_titles']:
            for title in sorted(summary['verified_titles']):
                self.stdout.write(f'  - {title}')
        else:
            self.stdout.write('  - none')

        self.stdout.write('\nEligibility reasons:')
        if summary['eligibility_reasons']:
            for reason in summary['eligibility_reasons']:
                self.stdout.write(f'  - {reason}')
        else:
            self.stdout.write('  - All criteria matched')

    def build_status(self, user):
        cms = CMSSettings.objects.filter(pk=1).first()
        required_requirements = (cms.admission_requirements if cms and cms.admission_requirements else [])

        if required_requirements:
            required_items = [
                {
                    'title': req.get('title', '').strip(),
                    'key': _title_to_key(req.get('title', '')),
                    'required': bool(req.get('required', True)),
                }
                for req in required_requirements
                if req.get('title', '').strip() and req.get('required', True)
            ]
        else:
            required_items = [
                {'title': display_name, 'key': doc_type, 'required': True}
                for doc_type, display_name in Document.DOCUMENT_TYPE_CHOICES
            ]

        required_n = len(required_items)

        personal = PersonalDetails.objects.filter(user=user).first()
        if personal:
            full_name = f'{personal.first_name} {personal.last_name}'.strip()
        else:
            full_name = user.get_full_name() or user.email or user.username

        app = getattr(user, 'application', None)

        verified_titles = set()
        uploaded_titles = set()
        for doc in Document.objects.filter(user=user):
            doc_key = _title_to_key(doc.document_type)
            if doc_key:
                uploaded_titles.add(doc_key)

        for verification in DocumentVerification.objects.filter(
            document__user=user,
            status='verified',
        ).select_related('document'):
            doc_key = _title_to_key(verification.document.document_type)
            if doc_key:
                verified_titles.add(doc_key)

        documents_uploaded = len([item for item in required_items if item['key'] in verified_titles])
        missing_documents = []
        for item in required_items:
            if item['key'] not in verified_titles:
                if item['key'] in uploaded_titles:
                    missing_documents.append(f"{item['title']} (uploaded but not yet verified)")
                else:
                    missing_documents.append(f"{item['title']} (not submitted)")

        cor = CORSubmission.objects.filter(user=user).order_by('-uploaded_at').first()
        cor_uploaded = bool(cor and cor.status == 'Verified')

        grade_submission = GradeSubmission.objects.filter(user=user).order_by('-uploaded_at').first()
        failing_grades = 0
        failing_subjects = []
        gwa = None
        if grade_submission:
            if grade_submission.gpa is not None:
                gwa = float(grade_submission.gpa)
            for entry in GradeEntry.objects.filter(submission=grade_submission):
                if entry.grade is not None and entry.grade > Decimal('2.00'):
                    failing_grades += 1
                    failing_subjects.append(entry.title)

        eligibility_reasons = []
        if missing_documents:
            eligibility_reasons.append(f"Missing documents: {', '.join(missing_documents)}")
        if not cor_uploaded:
            eligibility_reasons.append('COR is not verified')
        if failing_grades > 0:
            subject_list = ', '.join(failing_subjects[:5])
            reason = f'{failing_grades} failing grade(s)'
            if subject_list:
                reason = f'{reason}: {subject_list}'
            eligibility_reasons.append(reason)
        if gwa is not None and gwa > 2.0:
            eligibility_reasons.append(f'GWA {gwa:.2f} is above 2.00')

        is_eligible = not eligibility_reasons

        return {
            'full_name': full_name,
            'student_id': app.application_id if app else user.username,
            'documents_uploaded': documents_uploaded,
            'documents_required': required_n,
            'required_items': required_items,
            'uploaded_titles': uploaded_titles,
            'verified_titles': verified_titles,
            'missing_documents': missing_documents,
            'cor_uploaded': cor_uploaded,
            'failing_grades': failing_grades,
            'failing_subjects': failing_subjects,
            'gwa': gwa,
            'eligibility_reasons': eligibility_reasons,
            'is_eligible': is_eligible,
        }