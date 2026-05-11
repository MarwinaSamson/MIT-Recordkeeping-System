import json
import logging
 
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
 
from ..models import Application, DocumentVerification, AdminProfile, CMSSettings
from students_app.models import Document
 
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
DOCUMENT_TYPE_LABELS = {
    'deans_recommendation': "Dean's Recommendation",
    'tor': 'Transcript of Records',
    'honorable_dismissal': 'Honorable Dismissal',
    'psa': 'PSA (Live Birth)',
    'gsat': 'Graduate School Admission Test',
}
 
 
def is_superuser(user):
    return user.is_superuser
 

# All required document types — used to detect missing submissions
REQUIRED_DOCUMENT_TYPES = list(DOCUMENT_TYPE_LABELS.keys())


def _build_application_list():
    """
    Build application list matching documents against CMS admission_requirements
    by title — consistent with how documents_view.py saves Document.document_type.
    """
    from admin_app.models import CMSSettings
    from students_app.models import EducationalBackground, PersonalDetails, PrivacyConsent, WorkingStudent
    
    cms = CMSSettings.objects.filter(pk=1).first()
    admission_requirements = cms.admission_requirements if cms else []

    apps = []
    for app in Application.objects.select_related('user').order_by('-submission_date'):
        personal = PersonalDetails.objects.filter(user=app.user).first()
        working = WorkingStudent.objects.filter(user=app.user).first()
        privacy = PrivacyConsent.objects.filter(user=app.user, agreed=True).first()
        education_levels = {
            level.level: level
            for level in EducationalBackground.objects.filter(user=app.user)
        }
        submitted_docs = Document.objects.filter(user=app.user)

        student_curriculum = ''
        college_bg = education_levels.get('college')
        graduate_bg = education_levels.get('graduate')
        if college_bg and college_bg.mit_curriculum:
            student_curriculum = college_bg.mit_curriculum
        elif graduate_bg and graduate_bg.mit_curriculum:
            student_curriculum = graduate_bg.mit_curriculum

        # Key submitted docs by document_type (which equals the requirement title)
        submitted_by_title = {doc.document_type: doc for doc in submitted_docs}

        docs_list = []

        for req in admission_requirements:
            title       = req.get('title', '')
            description = req.get('description', '')
            number      = req.get('number', '')

            if title in submitted_by_title:
                doc = submitted_by_title[title]
                try:
                    verification = DocumentVerification.objects.get(document=doc)
                    status      = verification.get_status_display()
                    verified_by = (
                        verification.verified_by.get_full_name()
                        if verification.verified_by else ''
                    )
                    verified_on = (
                        verification.verified_at.strftime('%Y-%m-%d')
                        if verification.verified_at else ''
                    )
                except DocumentVerification.DoesNotExist:
                    status      = 'Pending Review'
                    verified_by = ''
                    verified_on = ''

                docs_list.append({
                    'id':          doc.id,
                    'name':        title,
                    'type':        title,
                    'description': description,
                    'reqNumber':   number,
                    'status':      status,
                    'missing':     False,
                    'uploadDate':  doc.uploaded_at.strftime('%Y-%m-%d'),
                    'verifiedBy':  verified_by,
                    'verifiedOn':  verified_on,
                    'fileUrl':     doc.file.url if doc.file else '',
                    'issues':      [],
                })
            else:
                # Requirement exists in CMS but student has not uploaded it
                docs_list.append({
                    'id':          None,
                    'name':        title,
                    'type':        title,
                    'description': description,
                    'reqNumber':   number,
                    'status':      'Missing',
                    'missing':     True,
                    'uploadDate':  '',
                    'verifiedBy':  '',
                    'verifiedOn':  '',
                    'fileUrl':     '',
                    'issues':      ['Document not yet submitted by student'],
                })

        # Catch any docs the student uploaded that don't match any CMS requirement
        # (e.g. uploaded before admin changed the requirements list)
        cms_titles = {req.get('title', '') for req in admission_requirements}
        for doc in submitted_docs:
            if doc.document_type not in cms_titles:
                try:
                    verification = DocumentVerification.objects.get(document=doc)
                    status      = verification.get_status_display()
                    verified_by = verification.verified_by.get_full_name() if verification.verified_by else ''
                    verified_on = verification.verified_at.strftime('%Y-%m-%d') if verification.verified_at else ''
                except DocumentVerification.DoesNotExist:
                    status      = 'Pending Review'
                    verified_by = ''
                    verified_on = ''

                docs_list.append({
                    'id':          doc.id,
                    'name':        doc.document_type,
                    'type':        doc.document_type,
                    'description': '',
                    'reqNumber':   '',
                    'status':      status,
                    'missing':     False,
                    'uploadDate':  doc.uploaded_at.strftime('%Y-%m-%d'),
                    'verifiedBy':  verified_by,
                    'verifiedOn':  verified_on,
                    'fileUrl':     doc.file.url if doc.file else '',
                    'issues':      [],
                })

        # Try to resolve a longer program description from the Program table
        program_description = ''
        try:
            from ..models import Program as _Program
            prog = _Program.objects.filter(name__iexact=app.program).first()
            if not prog:
                prog = _Program.objects.filter(program_label__iexact=app.program).first()
            if not prog:
                prog = _Program.objects.filter(program_label__icontains=app.program).first()
            if not prog:
                prog = _Program.objects.filter(name__icontains=app.program).first()
            program_description = prog.description if prog else ''
        except Exception:
            program_description = ''

        apps.append({
            'id':              app.application_id,
            'user_id':         app.user.id,
            'name':            app.get_full_name(),
            'email':           app.user.email,
            'mobile':          app.get_contact_number(),
            'course':          program_description or app.program,
            'program_description': program_description,
            'status':          app.status,
            'submission_date': app.submission_date.strftime('%Y-%m-%d'),
            'submissionDate':  app.submission_date.strftime('%Y-%m-%d'),
            'last_activity':   app.last_activity.strftime('%Y-%m-%d'),
            'lastActivity':    app.last_activity.strftime('%Y-%m-%d'),
            'documents':       submitted_docs.count(),
            'docs':            docs_list,
            'remarks':         app.remarks,
            'student_curriculum': student_curriculum,
            'curriculum':      app.curriculum or student_curriculum,
            'personal': {
                'first_name': personal.first_name if personal else '',
                'middle_name': personal.middle_name if personal else '',
                'last_name': personal.last_name if personal else '',
                'full_name': app.get_full_name(),
                'dob': personal.dob.strftime('%Y-%m-%d') if personal and personal.dob else '',
                'age': personal.age if personal and personal.age is not None else '',
                'gender': personal.gender if personal else '',
                'civil_status': personal.civil_status if personal else '',
                'place_of_birth': personal.place_of_birth if personal else '',
                'religion': personal.religion if personal else '',
                'religion_other': personal.religion_other if personal else '',
                'ethnicity': personal.ethnicity if personal else '',
                'ethnicity_other': personal.ethnicity_other if personal else '',
                'nationality': personal.nationality if personal else '',
                'nationality_other': personal.nationality_other if personal else '',
                'disability': personal.disability if personal else '',
                'disability_other': personal.disability_other if personal else '',
                'permanent_address': personal.permanent_address if personal else '',
                'current_address': personal.current_address if personal else '',
                'contact_number': personal.contact_number if personal else '',
                'email': personal.email if personal else app.user.email,
                'name_of_parent': personal.name_of_parent if personal else '',
                'relationship': personal.relationship if personal else '',
                'parent_income': personal.parent_income if personal else '',
                'name_of_spouse': personal.name_of_spouse if personal else '',
                'spouse_contact_number': personal.spouse_contact_number if personal else '',
                'spouse_income': personal.spouse_income if personal else '',
            },
            'education': {
                'elementary': {
                    'school_name': (education_levels.get('elementary').school_name if education_levels.get('elementary') else ''),
                    'degree_course': (education_levels.get('elementary').degree_course if education_levels.get('elementary') else ''),
                    'year_completed': (education_levels.get('elementary').year_completed if education_levels.get('elementary') else ''),
                },
                'secondary': {
                    'school_name': (education_levels.get('secondary').school_name if education_levels.get('secondary') else ''),
                    'degree_course': (education_levels.get('secondary').degree_course if education_levels.get('secondary') else ''),
                    'year_completed': (education_levels.get('secondary').year_completed if education_levels.get('secondary') else ''),
                },
                'college': {
                    'school_name': (education_levels.get('college').school_name if education_levels.get('college') else ''),
                    'degree_course': (education_levels.get('college').degree_course if education_levels.get('college') else ''),
                    'year_completed': (education_levels.get('college').year_completed if education_levels.get('college') else ''),
                    'scholarship': (education_levels.get('college').scholarship if education_levels.get('college') else ''),
                    'mit_curriculum': (education_levels.get('college').mit_curriculum if education_levels.get('college') else ''),
                },
                'graduate': {
                    'school_name': (education_levels.get('graduate').school_name if education_levels.get('graduate') else ''),
                    'degree_course': (education_levels.get('graduate').degree_course if education_levels.get('graduate') else ''),
                    'year_completed': (education_levels.get('graduate').year_completed if education_levels.get('graduate') else ''),
                    'scholarship': (education_levels.get('graduate').scholarship if education_levels.get('graduate') else ''),
                    'mit_curriculum': (education_levels.get('graduate').mit_curriculum if education_levels.get('graduate') else ''),
                },
                'scholarship': (education_levels.get('college').scholarship if education_levels.get('college') and education_levels.get('college').scholarship else ''),
                'mit_curriculum': (
                    education_levels.get('college').mit_curriculum
                    if education_levels.get('college') and education_levels.get('college').mit_curriculum
                    else ''
                ),
            },
            'working': {
                'is_employed': working.is_employed if working else False,
                'position': working.position if working else '',
                'monthly_income': working.monthly_income if working else '',
                'employment_status': working.employment_status if working else '',
                'employment_status_other': working.employment_status_other if working else '',
                'employer_name': working.employer_name if working else '',
                'employer_address': working.employer_address if working else '',
                'employer_contact': working.employer_contact if working else '',
                'employer_classification': working.employer_classification if working else '',
                'employer_classification_other': working.employer_classification_other if working else '',
            },
            'privacy': {
                'agreed': bool(privacy.agreed) if privacy else False,
                'name': privacy.name if privacy else '',
                'signed_at': privacy.signed_at.strftime('%Y-%m-%d %H:%M') if privacy and privacy.signed_at else '',
                'ip_address': privacy.ip_address if privacy else '',
                'user_agent': privacy.user_agent if privacy else '',
                'form_version': privacy.form_version if privacy else '',
            },
        })

    return apps
 
# ---------------------------------------------------------------------------
# Page view  (standalone – used only if you want a dedicated URL)
# ---------------------------------------------------------------------------
 
@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def document_verification_page(request):
    """
    Renders the Document Verification page as a standalone view.
 
    You can also keep the section inside admin_dashboard.html by
    using {% include 'admin_app/document_verification.html' %} and
    passing `all_applications` from the dashboard view — in that
    case you do NOT need this view at all.
    """
    all_applications = _build_application_list()
 
    admin_profile_picture = None
    try:
        profile = AdminProfile.objects.get(user=request.user)
        if profile.profile_picture:
            admin_profile_picture = profile.profile_picture.url
    except AdminProfile.DoesNotExist:
        pass
 
    context = {
        'page_title':          'Document Verification',
        'admin_name':          request.user.get_full_name() or request.user.username,
        'admin_email':         request.user.email,
        'admin_profile_picture': admin_profile_picture,
        'all_applications':    json.dumps(all_applications),
        'cms':                 CMSSettings.objects.filter(pk=1).first() or CMSSettings(),
    }
    return render(request, 'admin_app/document_verification.html', context)
 
 
# ---------------------------------------------------------------------------
# COR (Certificate of Registration) API views
# ---------------------------------------------------------------------------
 
@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(['GET'])
def get_cor_submissions(request):
    """
    GET /admin-panel/api/cor-submissions/
 
    Returns all COR submissions as JSON.
    Expects a CORSubmission model (or similar) in your app.
    Adjust the import and queryset to match your actual model.
    """
    try:
        # ------------------------------------------------------------------
        # Replace the block below with your real model import + queryset.
        # Example assumes a model like:
        #
        #   class CORSubmission(models.Model):
        #       user         = ForeignKey(User, ...)
        #       semester     = CharField(...)
        #       school_year  = CharField(...)
        #       cor_file     = FileField(...)
        #       status       = CharField(choices=[...], default='Pending')
        #       admin_remarks = TextField(blank=True)
        #       uploaded_at  = DateTimeField(auto_now_add=True)
        # ------------------------------------------------------------------
        from students_app.models import CORSubmission  # adjust import path
 
        submissions = []
        for s in CORSubmission.objects.select_related('user').order_by('-uploaded_at'):
            app = Application.objects.filter(user=s.user).first()
            submissions.append({
                'id':            s.id,
                'student_name':  s.user.get_full_name(),
                'student_id':    app.application_id if app else '',
                'course':        app.program if app else '',
                'semester':      s.semester,
                'school_year':   s.school_year,
                'status':        s.status,
                'admin_remarks': s.admin_remarks or '',
                'cor_file_url':  s.cor_file.url if s.cor_file else '',
                'uploaded_at':   s.uploaded_at.isoformat(),
            })
 
        return JsonResponse({'success': True, 'submissions': submissions})
 
    except ImportError:
        # Model not yet created – return empty list so the frontend degrades
        # gracefully instead of throwing a 500.
        logger.warning('CORSubmission model not found. Returning empty list.')
        return JsonResponse({'success': True, 'submissions': []})
 
    except Exception as exc:
        logger.exception('Error fetching COR submissions: %s', exc)
        return JsonResponse({'success': False, 'message': str(exc)}, status=500)
 
 
@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(['POST'])
def update_cor_submission(request, submission_id):
    """
    POST /admin-panel/api/cor-submissions/<id>/update/
 
    Body (JSON):
        { "status": "Verified" | "Rejected", "admin_remarks": "..." }
    """
    try:
        from students_app.models import CORSubmission  # adjust import path
 
        data   = json.loads(request.body)
        status  = data.get('status', '').strip()
        remarks = data.get('admin_remarks', '').strip()
 
        if status not in ('Verified', 'Rejected', 'Pending'):
            return JsonResponse(
                {'success': False, 'message': 'Invalid status value.'}, status=400
            )
 
        submission = CORSubmission.objects.get(pk=submission_id)
        submission.status        = status
        submission.admin_remarks = remarks
        submission.save(update_fields=['status', 'admin_remarks'])
 
        return JsonResponse({
            'success': True,
            'message': f'COR {status.lower()} successfully.',
        })
 
    except ImportError:
        return JsonResponse(
            {'success': False, 'message': 'CORSubmission model not found.'}, status=500
        )
    except CORSubmission.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Submission not found.'}, status=404)
    except Exception as exc:
        logger.exception('Error updating COR submission: %s', exc)
        return JsonResponse({'success': False, 'message': str(exc)}, status=500)
 
 
# ---------------------------------------------------------------------------
# Grades API views
# ---------------------------------------------------------------------------
 
@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(['GET'])
def get_grade_submissions(request):
    """
    GET /admin-panel/api/grade-submissions/
 
    Returns all grade submissions as JSON.
    Adjust the import to match your actual model.
    """
    try:
        # ------------------------------------------------------------------
        # Replace with your real model.  Example structure:
        #
        #   class GradeSubmission(models.Model):
        #       user          = ForeignKey(User, ...)
        #       semester      = CharField(...)
        #       school_year   = CharField(...)
        #       gpa           = DecimalField(null=True, blank=True)
        #       screenshot    = FileField(null=True, blank=True)
        #       status        = CharField(choices=[...], default='Pending')
        #       admin_remarks = TextField(blank=True)
        #       uploaded_at   = DateTimeField(auto_now_add=True)
        #
        #   class GradeEntry(models.Model):
        #       submission    = ForeignKey(GradeSubmission, ...)
        #       code          = CharField(...)
        #       title         = CharField(...)
        #       units         = PositiveIntegerField()
        #       grade         = DecimalField(null=True, blank=True)
        #       remarks       = CharField(blank=True)
        # ------------------------------------------------------------------
        from students_app.models import GradeSubmission  # adjust import path
 
        submissions = []
        for s in GradeSubmission.objects.select_related('user').order_by('-uploaded_at'):
            app = Application.objects.filter(user=s.user).first()
 
            # Build per-subject grade list if a related model exists
            grades = []
            if hasattr(s, 'gradeentry_set'):
                for entry in s.gradeentry_set.all():
                    grades.append({
                        'code':    entry.code,
                        'title':   entry.title,
                        'units':   entry.units,
                        'grade':   float(entry.grade) if entry.grade is not None else None,
                        'remarks': entry.remarks or '',
                    })
 
            submissions.append({
                'id':             s.id,
                'student_name':   s.user.get_full_name(),
                'student_id':     app.application_id if app else '',
                'course':         app.program if app else '',
                'semester':       s.semester,
                'school_year':    s.school_year,
                'gpa':            float(s.gpa) if s.gpa is not None else None,
                'status':         s.status,
                'admin_remarks':  s.admin_remarks or '',
                'screenshot_url': s.screenshot.url if s.screenshot else '',
                'uploaded_at':    s.uploaded_at.isoformat(),
                'grades':         grades,
                'subject_count':  len(grades),
            })
 
        return JsonResponse({'success': True, 'submissions': submissions})
 
    except ImportError:
        logger.warning('GradeSubmission model not found. Returning empty list.')
        return JsonResponse({'success': True, 'submissions': []})
 
    except Exception as exc:
        logger.exception('Error fetching grade submissions: %s', exc)
        return JsonResponse({'success': False, 'message': str(exc)}, status=500)
 
 
@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(['POST'])
def update_grade_submission(request, submission_id):
    """
    POST /admin-panel/api/grade-submissions/<id>/update/
 
    Body (JSON):
        { "status": "Acknowledged" | "Flagged" | "Pending", "admin_remarks": "..." }
    """
    try:
        from students_app.models import GradeSubmission  # adjust import path
 
        data    = json.loads(request.body)
        status  = data.get('status', '').strip()
        remarks = data.get('admin_remarks', '').strip()
 
        if status not in ('Acknowledged', 'Flagged', 'Pending'):
            return JsonResponse(
                {'success': False, 'message': 'Invalid status value.'}, status=400
            )
 
        submission = GradeSubmission.objects.get(pk=submission_id)
        submission.status        = status
        submission.admin_remarks = remarks
        submission.save(update_fields=['status', 'admin_remarks'])
 
        return JsonResponse({
            'success': True,
            'message': f'Grades {status.lower()} successfully.',
        })
 
    except ImportError:
        return JsonResponse(
            {'success': False, 'message': 'GradeSubmission model not found.'}, status=500
        )
    except GradeSubmission.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Submission not found.'}, status=404)
    except Exception as exc:
        logger.exception('Error updating grade submission: %s', exc)
        return JsonResponse({'success': False, 'message': str(exc)}, status=500)