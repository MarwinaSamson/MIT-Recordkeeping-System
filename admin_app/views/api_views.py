"""
API views for admin dashboard actions.
Handles document verification, rejection, and application status updates.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
import json

from ..models import Application, DocumentVerification, AdminActivityLog, AdminProfile, SchoolYear, Semester, AdminNotification
from students_app.models import Document
from ..models import Prospectus, ProspectusYear, ProspectusSemester, ProspectusSubject, Program

def is_superuser(user):
    """Check if user is a superuser."""
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admission_semesters(request):
    """Return semesters from the Semester table, including the active row."""
    try:
        qs = Semester.objects.select_related('school_year').order_by('school_year__name', 'semester_number')
        data = [
            {
                'id': semester.pk,
                'name': semester.name,
                'semester_number': semester.semester_number,
                'school_year': semester.school_year.name,
                'is_active': semester.is_active,
            }
            for semester in qs
        ]
        return JsonResponse({'success': True, 'semesters': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admission_school_years(request):
    """Return non-archived school years for admin dropdowns."""
    try:
        qs = SchoolYear.objects.filter(is_archived=False).order_by('-name')
        data = [{'id': sy.pk, 'name': sy.name, 'is_active': sy.is_active} for sy in qs]
        return JsonResponse({'success': True, 'school_years': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admission_curricula(request):
    """Return active prospectuses as curricula options."""
    try:
        qs = Prospectus.objects.select_related('program').filter(is_active=True).order_by('-created_at')
        data = [{'id': p.pk, 'name': p.name, 'program_name': p.program.name if p.program else '', 'description': p.description} for p in qs]
        return JsonResponse({'success': True, 'curricula': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_active_school_year_with_semester(request):
    """Return active school year with its active semester."""
    try:
        active_sy = SchoolYear.objects.filter(is_active=True).first()
        if not active_sy:
            return JsonResponse({
                'success': False, 
                'message': 'No active school year set.'
            }, status=400)
        
        active_semester = Semester.objects.filter(school_year=active_sy, is_active=True).first()
        
        data = {
            'school_year': {
                'id': active_sy.id,
                'name': active_sy.name,
                'is_active': active_sy.is_active
            },
            'active_semester': {
                'name': active_semester.name if active_semester else None,
                'semester_number': active_semester.semester_number if active_semester else None
            } if active_semester else None
        }
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_student_curriculum(request, user_id):
    """Fetch student's MIT curriculum from EducationalBackground (graduate level)."""
    try:
        from students_app.models import EducationalBackground
        
        # Try to get from graduate level first, then fall back to any level
        edu = EducationalBackground.objects.filter(
            user_id=user_id, 
            level='graduate',
            mit_curriculum__isnull=False
        ).first()
        
        if not edu:
            # Fallback: get from any education level with mit_curriculum
            edu = EducationalBackground.objects.filter(
                user_id=user_id,
                mit_curriculum__isnull=False
            ).first()
        
        curriculum = edu.mit_curriculum if edu else ''
        
        return JsonResponse({
            'success': True,
            'curriculum': curriculum
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'curriculum': '',
            'message': str(e)
        })


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def verify_document(request):
    """Verify a document and update its status."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')

        if not app_id or not doc_id:
            return JsonResponse({
                'success': False,
                'message': f'Missing fields: application_id={app_id}, document_id={doc_id}'
            }, status=400)

        app = Application.objects.get(application_id=app_id)
        doc = Document.objects.get(id=doc_id)

        verification, created = DocumentVerification.objects.get_or_create(
            document=doc)
        verification.status = 'verified'
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='verified',
            application=app,
            document=doc,
            notes=f"Document verified."
        )

        # Auto-update application status when all submitted docs are verified
        total_docs = Document.objects.filter(user=app.user).count()
        verified_docs = DocumentVerification.objects.filter(
            document__user=app.user, status='verified'
        ).count()
        has_unverified = DocumentVerification.objects.filter(
            document__user=app.user
        ).exclude(status='verified').exists()
        auto_verified = (
            total_docs > 0
            and verified_docs == total_docs
            and not has_unverified
            and app.status not in ('rejected',)
        )
        if auto_verified:
            app.status = 'verified'
            app.save(update_fields=['status', 'last_activity'])

        return JsonResponse({
            'success': True,
            'message': f'Document verified successfully.',
            'status': 'verified',
            'application_status': app.status,
        })
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Application {app_id} not found.'}, status=404)
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Document {doc_id} not found.'}, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': str(e),
            'detail': traceback.format_exc()
        }, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reject_document(request):
    """Reject a document and record the reason."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')
        reason = data.get('reason', '').strip()

        if not app_id or not doc_id:
            return JsonResponse({
                'success': False,
                'message': f'Missing fields: application_id={app_id}, document_id={doc_id}'
            }, status=400)

        if not reason:
            return JsonResponse({
                'success': False,
                'message': 'Rejection reason is required.'
            }, status=400)

        app = Application.objects.get(application_id=app_id)
        doc = Document.objects.get(id=doc_id)

        verification, created = DocumentVerification.objects.get_or_create(
            document=doc)
        verification.status = 'rejected'
        verification.rejection_reason = reason
        verification.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='rejected',
            application=app,
            document=doc,
            notes=f"Document rejected: {reason}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Document rejected successfully.',
            'status': 'rejected'
        })
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Application {app_id} not found.'}, status=404)
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Document {doc_id} not found.'}, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': str(e),
            'detail': traceback.format_exc()
        }, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reset_document_verification(request):
    """Reset document verification status back to under review."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')

        if not app_id or not doc_id:
            return JsonResponse({
                'success': False,
                'message': f'Missing fields: application_id={app_id}, document_id={doc_id}'
            }, status=400)

        app = Application.objects.get(application_id=app_id)
        doc = Document.objects.get(id=doc_id)

        verification, created = DocumentVerification.objects.get_or_create(document=doc)
        old_status = verification.status
        verification.status = 'reviewing'
        verification.verified_by = None
        verification.verified_at = None
        verification.rejection_reason = ''
        verification.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='resubmit',
            application=app,
            document=doc,
            notes=f"Document verification reset from {old_status} to reviewing."
        )

        return JsonResponse({
            'success': True,
            'message': 'Document reset to Under Review.',
            'status': 'reviewing'
        })
    except Application.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Application {app_id} not found.'}, status=404)
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Document {doc_id} not found.'}, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'message': str(e),
            'detail': traceback.format_exc()
        }, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_application_status(request):
    """Update application status (verified, incomplete, etc.)."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        status = data.get('status')
        remarks = data.get('remarks', '')

        # Get the application
        app = Application.objects.get(application_id=app_id)
        app.status = status
        app.remarks = remarks
        app.last_activity = timezone.now()

        # Save admission details if provided (on verify)
        if 'semester' in data:
            app.semester = data.get('semester', '').strip()
        if 'year_admitted' in data:
            app.year_admitted = data.get('year_admitted', '').strip()
        if 'program_level' in data:
            app.program_level = data.get('program_level', '').strip()
        if 'curriculum_data' in data:
            app.curriculum_data = data.get('curriculum_data', {})
        if 'curriculum' in data:
            app.curriculum = (data.get('curriculum') or '').strip()

        app.save()

        # Log the activity
        action_map = {
            'verified': 'verified',
            'incomplete': 'incomplete',
            'rejected': 'rejected'
        }
        AdminActivityLog.objects.create(
            admin=request.user,
            action=action_map.get(status, 'note'),
            application=app,
            notes=f"Application status changed to {status}. {remarks}"
        )

        # Notify the applicant by email for important status changes
        try:
            from django.core.mail import send_mail
            from django.conf import settings

            notify_statuses = ['enrolled', 'rejected', 'accepted']
            if status in notify_statuses and app.user and app.user.email:
                full_name = getattr(app.user, 'get_full_name', None)
                full_name = full_name() if callable(full_name) else (app.user.email or '')
                if not full_name:
                    full_name = app.user.email

                if status == 'enrolled' or status == 'accepted':
                    subject = 'Application Accepted — Enrollment Confirmed'
                    message = f"Dear {full_name},\n\nCongratulations! Your application (ID: {app.application_id}) has been accepted and marked as enrolled.\n\nPlease check your admission portal for next steps and enrollment details.\n\nBest regards,\nAdmissions Office"
                else:
                    subject = 'Application Update — Decision Notice'
                    message = f"Dear {full_name},\n\nWe regret to inform you that your application (ID: {app.application_id}) has been rejected.\n\nIf you have questions, please contact the Admissions Office.\n\nBest regards,\nAdmissions Office"

                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                        recipient_list=[app.user.email],
                        fail_silently=False,
                    )
                    AdminActivityLog.objects.create(
                        admin=request.user,
                        action='note',
                        application=app,
                        notes=f"Sent {status} notification email to {app.user.email}."
                    )
                except Exception as e:
                    # Log failure but do not prevent API response
                    print(f"Failed to send status email to {app.user.email}: {e}")
        except Exception:
            # Keep silent on notification import issues
            pass

        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {status}.',
            'status': status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_remarks(request):
    """Update application remarks."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        remarks = data.get('remarks', '')

        # Get the application
        app = Application.objects.get(application_id=app_id)
        app.remarks = remarks
        app.last_activity = timezone.now()
        app.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=app,
            notes=f"Remarks updated: {remarks}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Remarks updated successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_admin_profile(request):
    """Update admin profile information (first name, last name, email)."""
    try:
        data = json.loads(request.body)
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()

        # Validate inputs
        if not first_name or not last_name or not email:
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)

        # Check if email is already used by another user
        from django.contrib.auth.models import User
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already in use.'
            }, status=400)

        # Update user profile
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='profile_updated',
            notes=f"Updated profile: {first_name} {last_name} ({email})"
        )

        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully.',
            'data': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'full_name': user.get_full_name()
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def upload_admin_photo(request):
    """Upload admin profile photo."""
    try:
        if 'photo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No photo file provided.'
            }, status=400)

        photo_file = request.FILES['photo']

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if photo_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'message': 'Only JPG, PNG, and WEBP images are allowed.'
            }, status=400)

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if photo_file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'File size must not exceed 5MB.'
            }, status=400)

        # Get or create admin profile
        admin_profile, created = AdminProfile.objects.get_or_create(
            user=request.user)

        # Delete old photo if exists
        if admin_profile.profile_picture:
            if default_storage.exists(admin_profile.profile_picture.name):
                default_storage.delete(admin_profile.profile_picture.name)

        # Save new photo
        admin_profile.profile_picture = photo_file
        admin_profile.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='photo_updated',
            notes=f"Changed profile photo - {photo_file.name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Profile photo updated successfully.',
            'data': {
                'photo_url': admin_profile.profile_picture.url
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def list_user_accounts(request):
    """List user accounts for Account Management tab."""
    search = request.GET.get('q', '').strip()

    qs = User.objects.all().order_by('-date_joined')
    if search:
        qs = qs.filter(
            models.Q(username__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search)
        )

    users = [{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'access': 'admin' if user.is_superuser else 'student',
        'is_active': user.is_active,
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never',
        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
    } for user in qs]

    return JsonResponse({'success': True, 'data': users})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def create_user_account(request):
    """Create a new user account from Account Management tab."""
    try:
        data = json.loads(request.body)
        username = str(data.get('username', '')).strip()
        email = str(data.get('email', '')).strip()
        first_name = str(data.get('first_name', '')).strip()
        last_name = str(data.get('last_name', '')).strip()
        password = str(data.get('password', '')).strip()
        access = str(data.get('access', 'student')).strip().lower()
        is_active = bool(data.get('is_active', True))

        if not username or not email or not password:
            return JsonResponse({'success': False, 'message': 'Username, email, and password are required.'}, status=400)
        if access not in ['admin', 'student']:
            return JsonResponse({'success': False, 'message': 'Invalid access level.'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists.'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists.'}, status=400)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=(access == 'admin'),
            is_superuser=(access == 'admin'),
            is_active=is_active,
        )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='profile_updated',
            notes=f'Created user account: {user.username} ({access})'
        )
        return JsonResponse({'success': True, 'message': 'User account created successfully.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_user_account(request):
    """Update an existing user account from Account Management tab."""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'user_id is required.'}, status=400)

        user = User.objects.get(id=user_id)
        email = str(data.get('email', user.email)).strip()
        first_name = str(data.get('first_name', user.first_name)).strip()
        last_name = str(data.get('last_name', user.last_name)).strip()
        access = str(data.get('access', 'admin' if user.is_superuser else 'student')).strip().lower()
        is_active = bool(data.get('is_active', user.is_active))
        password = str(data.get('password', '')).strip()

        if access not in ['admin', 'student']:
            return JsonResponse({'success': False, 'message': 'Invalid access level.'}, status=400)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists.'}, status=400)
        if user.id == request.user.id and access != 'admin':
            return JsonResponse({'success': False, 'message': 'You cannot remove your own admin access.'}, status=400)

        user.email = email
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = access == 'admin'
        user.is_superuser = access == 'admin'
        user.is_active = is_active
        if password:
            user.set_password(password)
        user.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='profile_updated',
            notes=f'Updated user account: {user.username} ({access})'
        )
        return JsonResponse({'success': True, 'message': 'User account updated successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_user_account(request):
    """Delete a user account from Account Management tab."""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'user_id is required.'}, status=400)

        user = User.objects.get(id=user_id)
        if user.id == request.user.id:
            return JsonResponse({'success': False, 'message': 'You cannot delete your own account.'}, status=400)

        username = user.username
        user.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='profile_updated',
            notes=f'Deleted user account: {username}'
        )
        return JsonResponse({'success': True, 'message': 'User account deleted successfully.'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_cms_settings(request):
    """Update public homepage CMS settings."""
    try:
        data = json.loads(request.body)

        from ..models import CMSSettings

        # Get existing cms settings or use defaults
        try:
            cms = CMSSettings.objects.get(pk=1)
        except CMSSettings.DoesNotExist:
            CMSSettings.objects.create(pk=1)
            cms = CMSSettings.objects.get(pk=1)

        update_data = {
            'admissions_open': bool(data.get('admissions_open', cms.admissions_open)),
            'show_announcement': bool(data.get('show_announcement', cms.show_announcement)),
            'nav_subtitle': (data.get('nav_subtitle') or cms.nav_subtitle or '').strip(),
            'hero_badge': (data.get('hero_badge') or cms.hero_badge or '').strip(),
            'hero_heading1': (data.get('hero_heading1') or cms.hero_heading1 or '').strip(),
            'hero_heading2': (data.get('hero_heading2') or cms.hero_heading2 or '').strip(),
            'hero_tagline': (data.get('hero_tagline') or cms.hero_tagline or '').strip(),
            'app_window_ay': str(data.get('app_window_ay') or cms.app_window_ay or '').strip(),
            'app_window_enrollment': str(data.get('app_window_enrollment') or cms.app_window_enrollment or '').strip(),
            'app_window_deadline_year': str(data.get('app_window_deadline_year') or cms.app_window_deadline_year or '').strip(),
            'app_window_enrollment_year': str(data.get('app_window_enrollment_year') or cms.app_window_enrollment_year or '').strip(),
            'app_stat_val1': str(data.get('app_stat_val1') or cms.app_stat_val1 or '').strip(),
            'app_stat_label1': str(data.get('app_stat_label1') or cms.app_stat_label1 or '').strip(),
            'app_stat_val2': str(data.get('app_stat_val2') or cms.app_stat_val2 or '').strip(),
            'app_stat_label2': str(data.get('app_stat_label2') or cms.app_stat_label2 or '').strip(),
            'cta_heading': str(data.get('cta_heading') or cms.cta_heading or '').strip(),
            'cta_sublabel': str(data.get('cta_sublabel') or cms.cta_sublabel or '').strip(),
            'hero_bg_image_url': str(data.get('hero_bg_image_url') or cms.hero_bg_image_url or '').strip(),
            'contact_address': data.get('contact_address', cms.contact_address).strip(),
            'contact_phone': data.get('contact_phone', cms.contact_phone).strip(),
            'contact_email': data.get('contact_email', cms.contact_email).strip(),
            'contact_facebook': data.get('contact_facebook', cms.contact_facebook).strip(),
            'contact_hours': data.get('contact_hours', cms.contact_hours).strip(),
            # About page fields
            'about_hero_eyebrow': data.get('about_hero_eyebrow', cms.about_hero_eyebrow).strip(),
            'about_hero_title': data.get('about_hero_title', cms.about_hero_title).strip(),
            'about_hero_title_italic': data.get('about_hero_title_italic', cms.about_hero_title_italic).strip(),
            'about_hero_tagline': data.get('about_hero_tagline', cms.about_hero_tagline).strip(),
            'about_hero_badge': data.get('about_hero_badge', cms.about_hero_badge).strip(),
            'about_overview_text': data.get('about_overview_text', cms.about_overview_text).strip(),
            'about_info_institution': data.get('about_info_institution', cms.about_info_institution).strip(),
            'about_info_copc': data.get('about_info_copc', cms.about_info_copc).strip(),
            'about_info_ay': data.get('about_info_ay', cms.about_info_ay).strip(),
            'about_info_accred': data.get('about_info_accred', cms.about_info_accred).strip(),
            'about_ched_heading': data.get('about_ched_heading', cms.about_ched_heading).strip(),
            'about_ched_desc': data.get('about_ched_desc', cms.about_ched_desc).strip(),
            'about_stat1_val': data.get('about_stat1_val', cms.about_stat1_val).strip(),
            'about_stat1_lbl': data.get('about_stat1_lbl', cms.about_stat1_lbl).strip(),
            'about_stat2_val': data.get('about_stat2_val', cms.about_stat2_val).strip(),
            'about_stat2_lbl': data.get('about_stat2_lbl', cms.about_stat2_lbl).strip(),
            'about_stat3_val': data.get('about_stat3_val', cms.about_stat3_val).strip(),
            'about_stat3_lbl': data.get('about_stat3_lbl', cms.about_stat3_lbl).strip(),
            'about_stat4_val': data.get('about_stat4_val', cms.about_stat4_val).strip(),
            'about_stat4_lbl': data.get('about_stat4_lbl', cms.about_stat4_lbl).strip(),
            
        }

        # Only update date fields when explicitly included in the request to prevent
        # partial saves (e.g. hero image upload) from wiping enrollment/deadline dates.
        if 'application_deadline' in data:
            update_data['application_deadline'] = data['application_deadline'] or None
        if 'enrollment_start_date' in data:
            update_data['enrollment_start_date'] = data['enrollment_start_date'] or None
        if 'enrollment_end_date' in data:
            update_data['enrollment_end_date'] = data['enrollment_end_date'] or None

        # Validate and save announcements list [{text, duration}]
        raw_announcements = data.get('announcements', None)
        if raw_announcements is not None:
            cleaned = []
            for item in raw_announcements:
                text = str(item.get('text', '')).strip()
                try:
                    duration = max(3, int(item.get('duration', 5)))
                except (ValueError, TypeError):
                    duration = 5
                if text:
                    cleaned.append({'text': text, 'duration': duration})
            update_data['announcements'] = cleaned

        # Validate and save programs list [{name, degree, description, visible}]
        raw_programs = data.get('programs', None)
        if raw_programs is not None:
            cleaned_programs = []
            for p in raw_programs:
                name = str(p.get('name', '')).strip()
                degree = str(p.get('degree', '')).strip()
                description = str(p.get('description', '')).strip()
                visible = bool(p.get('visible', True))
                if name:
                    cleaned_programs.append({
                        'name': name,
                        'degree': degree,
                        'description': description,
                        'visible': visible,
                    })
            update_data['programs'] = cleaned_programs

        # Validate and save downloads list [{name, resource_type, file_name, url, file_type}]
        raw_downloads = data.get('downloads', None)
        if raw_downloads is not None:
            cleaned_downloads = []
            for d in raw_downloads:
                display_name = str(
                    d.get('resource_type', '') or d.get('name', '')
                ).strip()
                original_name = str(d.get('file_name', '')).strip()
                url = str(d.get('url', '')).strip()
                file_type = str(d.get('file_type', '')).strip()
                if display_name and url:
                    cleaned_downloads.append({
                        'name': display_name,
                        'resource_type': display_name,
                        'file_name': original_name or display_name,
                        'url': url,
                        'file_type': file_type,
                    })
            update_data['downloads'] = cleaned_downloads

        # Validate and save event slides list
        raw_event_slides = data.get('event_slides', None)
        if raw_event_slides is not None:
            cleaned_slides = []
            for slide in raw_event_slides:
                title = str(slide.get('title', '')).strip()
                if title:  # Only add if title exists
                    cleaned_slides.append({
                        'title': title,
                        'date': str(slide.get('date', '')).strip(),
                        'day_label': str(slide.get('day_label', '')).strip(),
                        'time': str(slide.get('time', '')).strip(),
                        'venue': str(slide.get('venue', '')).strip(),
                        'description': str(slide.get('desc', slide.get('description', ''))).strip(),
                        'image_url': str(slide.get('image_url', '')).strip(),
                        'audience': str(slide.get('audience', '')).strip(),
                        'featured': bool(slide.get('featured', False)),
                    })
            update_data['event_slides'] = cleaned_slides

        saved_calendar_event = None
        raw_calendar_events = data.get('calendar_events', None)
        if raw_calendar_events is not None:
            cleaned_events = []
            for evt in raw_calendar_events:
                title = str(evt.get('title', '')).strip()
                if title:  # Only add if title exists
                    cleaned_events.append({
                        'id': int(evt.get('id', 0)),
                        'month': int(evt.get('month', 1)),
                        'day': int(evt.get('day', 1)),
                        'title': title,
                        'type': str(evt.get('type', 'cr')).strip(),
                        'tag': str(evt.get('tag', '')).strip(),
                        'time': str(evt.get('time', '')).strip(),
                        'venue': str(evt.get('venue', '')).strip(),
                        'audience': str(evt.get('audience', '')).strip(),
                        'desc': str(evt.get('desc', '')).strip(),
                    })
            update_data['calendar_events'] = cleaned_events

        raw_calendar_event = data.get('calendar_event', None)
        if raw_calendar_event is not None:
            existing_events = cms.calendar_events or []
            title = str(raw_calendar_event.get('title', '')).strip()
            if title:
                evt_id = int(raw_calendar_event.get('id') or 0)
                if evt_id <= 0:
                    existing_ids = [int(e.get('id', 0)) for e in existing_events if e.get('id') is not None]
                    evt_id = max(existing_ids, default=0) + 1

                day_from = int(raw_calendar_event.get('day', 1))
                raw_day_to = raw_calendar_event.get('day_to')
                day_to = int(raw_day_to) if raw_day_to else None

                event = {
                    'id': evt_id,
                    'month': int(raw_calendar_event.get('month', 1)),
                    'day': day_from,
                    'day_to': day_to,
                    'title': title,
                    'type': str(raw_calendar_event.get('type', 'cr')).strip(),
                    'tag': str(raw_calendar_event.get('tag', '')).strip(),
                    'time': str(raw_calendar_event.get('time', '')).strip(),
                    'venue': str(raw_calendar_event.get('venue', '')).strip(),
                    'audience': str(raw_calendar_event.get('audience', '')).strip(),
                    'desc': str(raw_calendar_event.get('desc', '')).strip(),
                    'attachments': raw_calendar_event.get('attachments', []),
                }
                saved_calendar_event = event
                updated = False
                for idx, evt in enumerate(existing_events):
                    if int(evt.get('id', 0)) == evt_id:
                        existing_events[idx] = event
                        updated = True
                        break
                if not updated:
                    existing_events.append(event)
                update_data['calendar_events'] = existing_events

        raw_calendar_event_delete = data.get('calendar_event_delete', None)
        if raw_calendar_event_delete is not None:
            existing_events = cms.calendar_events or []
            delete_id = int(raw_calendar_event_delete.get('id') or 0)
            if delete_id > 0:
                update_data['calendar_events'] = [
                    evt for evt in existing_events if int(evt.get('id', 0)) != delete_id
                ]

        # Validate and save admission requirements list
        raw_admission_requirements = data.get('admission_requirements', None)
        if raw_admission_requirements is not None:
            cleaned_requirements = []
            for req in raw_admission_requirements:
                title = str(req.get('title', '')).strip()
                if title:  # Only add if title exists
                    cleaned_requirements.append({
                        'number': int(req.get('number', 1)),
                        'title': title,
                        'description': str(req.get('description', '')).strip(),
                        'required': bool(req.get('required', False)),    # ← ADD THIS
                        'multi_page': bool(req.get('multi_page', False)), # ← ADD THIS
                    })
            update_data['admission_requirements'] = cleaned_requirements

        # Validate and save about outcomes list [{number: int, title: str, description: str}]
        raw_about_outcomes = data.get('about_outcomes', None)
        if raw_about_outcomes is not None:
            cleaned_outcomes = []
            for outcome in raw_about_outcomes:
                try:
                    number = int(outcome.get('number', 0))
                except (ValueError, TypeError):
                    number = 0
                title = str(outcome.get('title', '')).strip()
                description = str(outcome.get('description', '')).strip()
                if title and number > 0:
                    cleaned_outcomes.append({
                        'number': number,
                        'title': title,
                        'description': description
                    })
            update_data['about_outcomes'] = cleaned_outcomes

        # Validate and save about objectives list [{title: str, description: str}]
        raw_about_objectives = data.get('about_objectives', None)
        if raw_about_objectives is not None:
            cleaned_objectives = []
            for obj in raw_about_objectives:
                title = str(obj.get('title', '')).strip()
                description = str(obj.get('description', '')).strip()
                if title:
                    cleaned_objectives.append({
                        'title': title,
                        'description': description
                    })
            update_data['about_objectives'] = cleaned_objectives

        # Flat course catalog for About page (Others → Curriculum Structure) [{code, name, units, description}]
        raw_about_courses = data.get('about_courses', None)
        if raw_about_courses is not None:
            cleaned_about_courses = []
            if isinstance(raw_about_courses, list):
                for item in raw_about_courses:
                    if not isinstance(item, dict):
                        continue
                    code = str(item.get('code', '')).strip()
                    name = str(item.get('name', '')).strip()
                    description = str(item.get('description', '') or '').strip()
                    try:
                        units = int(item.get('units', 0))
                    except (ValueError, TypeError):
                        units = 0
                    if code and name and units > 0:
                        cleaned_about_courses.append({
                            'code': code,
                            'name': name,
                            'units': units,
                            'description': description,
                        })
            update_data['about_courses'] = cleaned_about_courses

        # Validate and save about faculty list [{name, title, bio, tags, photo_url}]
        raw_about_faculty = data.get('about_faculty', None)
        if raw_about_faculty is not None:
            cleaned_faculty = []
            for fac in raw_about_faculty:
                name = str(fac.get('name', '')).strip()
                title = str(fac.get('title', '')).strip()
                bio = str(fac.get('bio', '')).strip()
                photo_url = str(fac.get('photo_url', '') or '').strip()
                tags = fac.get('tags', [])
                if isinstance(tags, str):
                    tags = [tag.strip() for tag in tags.split(',') if tag.strip()]
                elif isinstance(tags, list):
                    tags = [str(tag).strip() for tag in tags if str(tag).strip()]
                else:
                    tags = []
                if name:
                    cleaned_faculty.append({
                        'name': name,
                        'title': title,
                        'bio': bio,
                        'tags': tags,
                        'photo_url': photo_url,
                    })
            update_data['about_faculty'] = cleaned_faculty

        # Use bulk update for better performance
        CMSSettings.objects.filter(pk=1).update(**update_data)

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Homepage CMS settings updated.'
        )

        message = 'CMS settings saved.'
        if raw_calendar_event is not None:
            message = 'Calendar event saved.'
        elif raw_calendar_event_delete is not None:
            message = 'Calendar event deleted.'

        response_payload = {'success': True, 'message': message}
        if saved_calendar_event is not None:
            response_payload['saved_calendar_event'] = saved_calendar_event
        return JsonResponse(response_payload)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def bulk_upload_cms_settings(request):
    """Bulk upload CMS content from admin CSV import."""
    try:
        data = json.loads(request.body)
        section = str(data.get('section', '')).strip()
        mode = str(data.get('mode', 'replace')).strip().lower()
        rows = data.get('rows', []) or []

        from ..models import CMSSettings

        cms, _ = CMSSettings.objects.get_or_create(pk=1)

        if section == 'announcements':
            cleaned = []
            for item in rows:
                text = str(item.get('text', '')).strip()
                if not text:
                    continue
                try:
                    duration = int(item.get('duration_sec', item.get('duration', 5)) or 5)
                except (ValueError, TypeError):
                    duration = 5
                cleaned.append({'text': text, 'duration': max(3, duration)})

            if mode == 'append':
                cms.announcements = (cms.announcements or []) + cleaned
            else:
                cms.announcements = cleaned

        elif section == 'events':
            existing = cms.calendar_events or []
            max_id = max([int(evt.get('id', 0)) for evt in existing] + [0])
            cleaned = []
            for item in rows:
                title = str(item.get('title', '')).strip()
                if not title:
                    continue
                month = int(item.get('month', 1) or 1)
                day = int(item.get('day', 1) or 1)
                evt_id = item.get('id')
                if evt_id is None or str(evt_id).strip() == '':
                    max_id += 1
                    evt_id = max_id
                cleaned.append({
                    'id': int(evt_id),
                    'month': max(1, min(12, month)),
                    'day': max(1, min(31, day)),
                    'title': title,
                    'type': str(item.get('type', 'cr')).strip(),
                    'tag': str(item.get('tag', '')).strip(),
                    'time': str(item.get('time', '')).strip(),
                    'venue': str(item.get('venue', '')).strip(),
                    'audience': str(item.get('audience', '')).strip(),
                    'desc': str(item.get('description', item.get('desc', ''))).strip(),
                })
            cms.calendar_events = (existing + cleaned) if mode == 'append' else cleaned

        elif section == 'requirements':
            existing = cms.admission_requirements or []
            next_num = max([int(req.get('number', 0)) for req in existing] + [0]) + 1
            cleaned = []
            for item in rows:
                title = str(item.get('requirement_name', item.get('title', ''))).strip()
                if not title:
                    continue
                description = str(item.get('hint_text', item.get('description', ''))).strip()
                cleaned.append({
                    'number': next_num,
                    'title': title,
                    'description': description,
                    'required': bool(item.get('required', False)),    # ← ADD THIS
                    'multi_page': bool(item.get('multi_page', False)), # ← ADD THIS
                })
                next_num += 1
            cms.admission_requirements = (existing + cleaned) if mode == 'append' else cleaned

        elif section == 'outcomes':
            existing = cms.program_outcomes or []
            next_num = max([int(out.get('number', 0)) for out in existing] + [0]) + 1
            cleaned = []
            for item in rows:
                title = str(item.get('outcome_title', item.get('title', ''))).strip()
                if not title:
                    continue
                description = str(item.get('outcome_description', item.get('description', ''))).strip()
                cleaned.append({
                    'number': next_num,
                    'title': title,
                    'description': description,
                })
                next_num += 1
            cms.program_outcomes = (existing + cleaned) if mode == 'append' else cleaned

        elif section == 'objectives':
            existing = cms.program_objectives or []
            cleaned = []
            for item in rows:
                text = str(item.get('objective_text', '')).strip()
                if not text:
                    continue
                cleaned.append({'title': text, 'description': ''})
            cms.program_objectives = (existing + cleaned) if mode == 'append' else cleaned

        else:
            return JsonResponse({
                'success': False,
                'message': 'Unsupported bulk upload section.'
            }, status=400)

        cms.save()
        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f'Bulk uploaded CMS section: {section}'
        )
        return JsonResponse({'success': True, 'message': 'Bulk upload saved.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def upload_cms_file(request):
    """Upload a file for CMS. Routes to different folders based on 'field' POST param."""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided.'
            }, status=400)

        file = request.FILES['file']
        field = request.POST.get('field', '')

        # Route to the appropriate upload folder
        if field == 'hero_bg_image':
            upload_folder = 'cms/hero'
            max_size = 10 * 1024 * 1024  # 10 MB
        elif field == 'event_image':
            upload_folder = 'cms/events'
            max_size = 10 * 1024 * 1024  # 10 MB
        else:
            upload_folder = 'downloads'
            max_size = 50 * 1024 * 1024  # 50 MB

        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': f'File size must not exceed {max_size // (1024 * 1024)} MB.'
            }, status=400)

        # Save file to media/<upload_folder>
        from django.core.files.storage import default_storage
        file_path = f'{upload_folder}/{file.name}'
        path = default_storage.save(file_path, file)
        file_url = default_storage.url(path)

        # Get file extension for type
        import os
        _, ext = os.path.splitext(file.name)
        file_type = ext.lstrip('.').upper() if ext else 'FILE'

        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully.',
            'data': {
                'name': file.name,
                'url': file_url,
                'file_type': file_type
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error uploading file: {str(e)}'
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_enrollment_count(request):
    """Return the current verified enrollment count (for CMS Application Window card)."""
    try:
        active_sy = SchoolYear.objects.filter(is_active=True).first()
        if active_sy:
            count = Application.objects.filter(
                year_admitted=active_sy.name,
                status='verified'
            ).count()
        else:
            count = Application.objects.filter(status='verified').count()
        return JsonResponse({'success': True, 'count': count})
    except Exception as e:
        return JsonResponse({'success': False, 'count': 0, 'message': str(e)})


# ============== Student Requirement Notification APIs ==============

@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_requirement_types(request):
    """Get all active requirement types."""
    from ..models import RequirementType

    types = RequirementType.objects.filter(is_active=True).order_by('name')
    data = [{'id': t.id, 'name': t.name, 'description': t.description}
            for t in types]
    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def create_requirement_type(request):
    """Create a new requirement type."""
    from ..models import RequirementType

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return JsonResponse({'success': False, 'message': 'Requirement name is required.'}, status=400)

        # Check if already exists
        if RequirementType.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'message': 'A requirement type with this name already exists.'}, status=400)

        req_type = RequirementType.objects.create(
            name=name, description=description)

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            notes=f"Created requirement type: {name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Requirement type created successfully.',
            'data': {'id': req_type.id, 'name': req_type.name, 'description': req_type.description}
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_requirement_type(request):
    """Delete a requirement type."""
    from ..models import RequirementType

    try:
        data = json.loads(request.body)
        type_id = data.get('requirement_type_id')

        if not type_id:
            return JsonResponse({'success': False, 'message': 'Requirement type ID is required.'}, status=400)

        req_type = RequirementType.objects.get(id=type_id)
        name = req_type.name
        req_type.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            notes=f"Deleted requirement type: {name}"
        )

        return JsonResponse({'success': True, 'message': 'Requirement type deleted successfully.'})
    except RequirementType.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Requirement type not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_students_with_requirements(request):
    """Get list of students with missing requirements."""
    from ..models import StudentRequirement, RequirementType
    from django.contrib.auth.models import User

    # Get filter parameters
    status = request.GET.get('status', '')
    requirement_id = request.GET.get('requirement_id', '')

    requirements = StudentRequirement.objects.select_related(
        'user', 'requirement')

    if status:
        requirements = requirements.filter(status=status)
    if requirement_id:
        requirements = requirements.filter(requirement_id=requirement_id)

    # Group by student
    student_data = {}
    for req in requirements:
        user_id = req.user.id
        if user_id not in student_data:
            user = req.user
            # Get application info
            app = Application.objects.filter(user=user).first()
            student_data[user_id] = {
                'user_id': user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name() or user.email,
                'application_id': app.application_id if app else None,
                'requirements': []
            }

        student_data[user_id]['requirements'].append({
            'id': req.id,
            'requirement_id': req.requirement.id,
            'requirement_name': req.requirement.name,
            'status': req.status,
            'notes': req.notes,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': req.updated_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({'success': True, 'data': list(student_data.values())})


def _get_or_create_program_by_slug(slug):
    """Get Program DB record by slug, auto-creating from CMSSettings JSON if missing."""
    try:
        return Program.objects.get(slug=slug)
    except Program.DoesNotExist:
        from ..models import CMSSettings
        cms = CMSSettings.objects.filter(pk=1).first()
        if cms:
            prog_data = next((p for p in (cms.programs or []) if p.get('slug') == slug), None)
            if prog_data:
                program, _ = Program.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': prog_data['name'],
                        'program_label': prog_data.get('degree', ''),
                    },
                )
                return program
        return None


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def list_prospectuses_for_program(request, program_slug):
    """Return all prospectuses for a program, with nested years/semesters/subjects."""
    try:
        program = _get_or_create_program_by_slug(program_slug)
        if not program:
            return JsonResponse({'success': True, 'data': []})
        qs = program.prospectuses.all().order_by('-created_at')
        out = []
        for p in qs:
            years = []
            for y in p.years.all().order_by('order'):
                sems = []
                for s in y.semesters.all().order_by('order'):
                    subs = []
                    for sub in s.subjects.all().order_by('order'):
                        subs.append({
                            'id': sub.id,
                            'order': sub.order,
                            'code': sub.code,
                            'title': sub.title,
                            'prereq': sub.prereq,
                            'lec': sub.lec,
                            'lab': sub.lab,
                            'total': sub.total,
                            'grade': sub.grade,
                            'is_core': sub.is_core,
                            'is_spec': sub.is_specialization,
                            'desc': sub.description,
                        })
                    sems.append({'id': s.id, 'order': s.order, 'label': s.label, 'is_other_req': s.is_other_req, 'subjects': subs})
                years.append({'id': y.id, 'order': y.order, 'label': y.label, 'semesters': sems})
            out.append({
                'id': p.id,
                'name': p.name,
                'description': p.description,
                'college': p.college,
                'full_program_name': p.full_program_name,
                'cmo_ref': p.cmo_ref,
                'bor_ref': p.bor_ref,
                'effective_year': p.effective_year,
                'prepared_by_name': p.prepared_by_name,
                'prepared_by_title': p.prepared_by_title,
                'prepared_by_date': p.prepared_by_date,
                'noted_by_name': p.noted_by_name,
                'noted_by_title': p.noted_by_title,
                'noted_by_date': p.noted_by_date,
                'years': years,
            })
        return JsonResponse({'success': True, 'data': out})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def list_programs(request):
    """Return list of Program records."""
    try:
        qs = Program.objects.all().order_by('name')
        data = [
            {
                'id': p.id,
                'name': p.name,
                'program_label': p.program_label,
                'description': p.description,
            }
            for p in qs
        ]
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def create_prospectus(request):
    """Create a prospectus linked to a program by slug."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        program_slug = data.get('program_slug', '').strip()

        if not name:
            return JsonResponse({'success': False, 'message': 'Prospectus name is required.'}, status=400)
        if not program_slug:
            return JsonResponse({'success': False, 'message': 'program_slug is required.'}, status=400)

        program = _get_or_create_program_by_slug(program_slug)
        if not program:
            return JsonResponse({'success': False, 'message': 'Program not found. Please re-save the program first.'}, status=404)

        p = Prospectus.objects.create(
            program=program,
            name=name,
            description=description,
            college=data.get('college', '').strip(),
            full_program_name=data.get('full_program_name', '').strip(),
            cmo_ref=data.get('cmo_ref', '').strip(),
            bor_ref=data.get('bor_ref', '').strip(),
            effective_year=data.get('effective_year', '').strip(),
            prepared_by_name=data.get('prepared_by_name', '').strip(),
            prepared_by_title=data.get('prepared_by_title', '').strip(),
            prepared_by_date=data.get('prepared_by_date', '').strip(),
            noted_by_name=data.get('noted_by_name', '').strip(),
            noted_by_title=data.get('noted_by_title', '').strip(),
            noted_by_date=data.get('noted_by_date', '').strip(),
            created_by=request.user,
        )

        # Save years/semesters/subjects if provided during creation
        for y_idx, y in enumerate(data.get('years', [])):
            py = ProspectusYear.objects.create(
                prospectus=p, order=y_idx,
                label=y.get('label', f'Year {y_idx + 1}'),
            )
            for s_idx, s in enumerate(y.get('semesters', [])):
                ps = ProspectusSemester.objects.create(
                    year=py, order=s_idx,
                    label=s.get('label', f'Semester {s_idx + 1}'),
                    is_other_req=bool(s.get('is_other_req', False)),
                )
                for sub_idx, sub in enumerate(s.get('subjects', [])):
                    ProspectusSubject.objects.create(
                        semester=ps,
                        order=sub_idx,
                        code=sub.get('code', '').strip(),
                        title=sub.get('title', '').strip() or 'Untitled',
                        prereq=sub.get('prereq', '').strip(),
                        lec=int(sub.get('lec') or 0),
                        lab=int(sub.get('lab') or 0),
                        total=int(sub.get('total') or 0),
                        is_core=bool(sub.get('is_core', False)),
                        is_specialization=bool(sub.get('is_spec', False)),
                        description=str(sub.get('desc') or '').strip(),
                    )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='created_prospectus',
            notes=f'Created prospectus: {p.name} for {program.name}',
        )
        return JsonResponse({'success': True, 'message': 'Prospectus created.', 'id': p.id})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_prospectus(request, prospectus_id):
    """Replace all years/semesters/subjects for an existing prospectus."""
    try:
        data = json.loads(request.body)
        p = Prospectus.objects.get(id=prospectus_id)

        name = data.get('name', '').strip()
        if name:
            p.name = name
        p.description = data.get('description', p.description)
        p.college = data.get('college', p.college)
        p.full_program_name = data.get('full_program_name', p.full_program_name)
        p.cmo_ref = data.get('cmo_ref', p.cmo_ref)
        p.bor_ref = data.get('bor_ref', p.bor_ref)
        p.effective_year = data.get('effective_year', p.effective_year)
        p.prepared_by_name = data.get('prepared_by_name', p.prepared_by_name)
        p.prepared_by_title = data.get('prepared_by_title', p.prepared_by_title)
        p.prepared_by_date = data.get('prepared_by_date', p.prepared_by_date)
        p.noted_by_name = data.get('noted_by_name', p.noted_by_name)
        p.noted_by_title = data.get('noted_by_title', p.noted_by_title)
        p.noted_by_date = data.get('noted_by_date', p.noted_by_date)
        p.save(update_fields=['name', 'description', 'college', 'full_program_name', 'cmo_ref', 'bor_ref', 'effective_year',
                               'prepared_by_name', 'prepared_by_title', 'prepared_by_date',
                               'noted_by_name', 'noted_by_title', 'noted_by_date', 'updated_at'])

        # Replace all nested data
        p.years.all().delete()
        for y_idx, y in enumerate(data.get('years', [])):
            py = ProspectusYear.objects.create(prospectus=p, order=y_idx, label=y.get('label', f'Year {y_idx+1}'))
            for s_idx, s in enumerate(y.get('semesters', [])):
                ps = ProspectusSemester.objects.create(
                    year=py, order=s_idx, label=s.get('label', f'Semester {s_idx+1}'),
                    is_other_req=bool(s.get('is_other_req', False)),
                )
                for sub_idx, sub in enumerate(s.get('subjects', [])):
                    ProspectusSubject.objects.create(
                        semester=ps,
                        order=sub_idx,
                        code=sub.get('code', '').strip(),
                        title=sub.get('title', '').strip() or 'Untitled',
                        prereq=sub.get('prereq', '').strip(),
                        lec=int(sub.get('lec') or 0),
                        lab=int(sub.get('lab') or 0),
                        total=int(sub.get('total') or 0),
                        grade=str(sub.get('grade') or '').strip(),
                        is_core=bool(sub.get('is_core', False)),
                        is_specialization=bool(sub.get('is_spec', False)),
                        description=str(sub.get('desc') or '').strip(),
                    )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='updated_prospectus',
            notes=f'Updated prospectus: {p.name}',
        )
        return JsonResponse({'success': True, 'message': 'Prospectus updated.'})
    except Prospectus.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prospectus not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_prospectus(request, prospectus_id=None):
    try:
        data = json.loads(request.body) if request.body else {}
        pid = prospectus_id or data.get('id')
        if not pid:
            return JsonResponse({'success': False, 'message': 'Prospectus id required.'}, status=400)
        p = Prospectus.objects.get(id=pid)
        name = p.name
        p.delete()
        AdminActivityLog.objects.create(admin=request.user, action='deleted_prospectus', notes=f'Deleted prospectus: {name}')
        return JsonResponse({'success': True, 'message': 'Prospectus deleted.'})
    except Prospectus.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prospectus not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)




@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def add_student_requirement(request):
    """Add a missing requirement for a student."""
    from ..models import StudentRequirement, RequirementType, RequirementNotification
    from django.contrib.auth.models import User

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        requirement_id = data.get('requirement_id')
        notes = data.get('notes', '').strip()

        if not user_id or not requirement_id:
            return JsonResponse({'success': False, 'message': 'User ID and Requirement ID are required.'}, status=400)

        user = User.objects.get(id=user_id)
        requirement = RequirementType.objects.get(id=requirement_id)

        # Check if already exists
        if StudentRequirement.objects.filter(user=user, requirement=requirement).exists():
            return JsonResponse({'success': False, 'message': 'This requirement is already marked for this student.'}, status=400)

        student_req = StudentRequirement.objects.create(
            user=user,
            requirement=requirement,
            notes=notes,
            status='pending'
        )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=Application.objects.filter(user=user).first(),
            notes=f"Added missing requirement for {user.username}: {requirement.name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Requirement added successfully.',
            'data': {
                'id': student_req.id,
                'requirement_name': requirement.name,
                'status': student_req.status
            }
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
    except RequirementType.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Requirement type not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def remove_student_requirement(request):
    """Remove a missing requirement from a student."""
    from ..models import StudentRequirement

    try:
        data = json.loads(request.body)
        requirement_id = data.get('student_requirement_id')

        if not requirement_id:
            return JsonResponse({'success': False, 'message': 'Student requirement ID is required.'}, status=400)

        student_req = StudentRequirement.objects.get(id=requirement_id)
        user = student_req.user
        req_name = student_req.requirement.name
        student_req.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=Application.objects.filter(user=user).first(),
            notes=f"Removed missing requirement for {user.username}: {req_name}"
        )

        return JsonResponse({'success': True, 'message': 'Requirement removed successfully.'})
    except StudentRequirement.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student requirement not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_student_requirement_status(request):
    """Update the status of a student requirement."""
    from ..models import StudentRequirement

    try:
        data = json.loads(request.body)
        requirement_id = data.get('student_requirement_id')
        new_status = data.get('status')

        if not requirement_id or not new_status:
            return JsonResponse({'success': False, 'message': 'Requirement ID and status are required.'}, status=400)

        valid_statuses = ['pending', 'notified', 'submitted', 'waived']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status.'}, status=400)

        student_req = StudentRequirement.objects.get(id=requirement_id)
        old_status = student_req.status
        student_req.status = new_status

        if new_status == 'notified':
            student_req.notified_at = timezone.now()

        student_req.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=Application.objects.filter(
                user=student_req.user).first(),
            notes=f"Updated requirement status for {student_req.user.username}: {student_req.requirement.name} ({old_status} -> {new_status})"
        )

        return JsonResponse({
            'success': True,
            'message': 'Status updated successfully.',
            'data': {'status': student_req.status}
        })
    except StudentRequirement.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student requirement not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def send_requirement_notification(request):
    """Send a notification to a student about missing requirements."""
    from ..models import StudentRequirement, RequirementNotification
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        data = json.loads(request.body)
        student_requirement_ids = data.get('student_requirement_ids', [])
        message = data.get('message', '').strip()

        if not student_requirement_ids:
            return JsonResponse({'success': False, 'message': 'At least one student requirement is required.'}, status=400)

        if not message:
            return JsonResponse({'success': False, 'message': 'Notification message is required.'}, status=400)

        # Group requirements by user
        requirements_by_user = {}
        for req_id in student_requirement_ids:
            try:
                req = StudentRequirement.objects.get(id=req_id)
                user_id = req.user.id
                if user_id not in requirements_by_user:
                    requirements_by_user[user_id] = {
                        'user': req.user,
                        'requirements': [],
                        'req_ids': []
                    }
                requirements_by_user[user_id]['requirements'].append(
                    req.requirement.name)
                requirements_by_user[user_id]['req_ids'].append(req_id)
            except StudentRequirement.DoesNotExist:
                continue

        # Send notifications to each student
        notifications_sent = 0
        for user_id, user_data in requirements_by_user.items():
            user = user_data['user']
            req_names = ', '.join(user_data['requirements'])

            # Update status to notified
            for req_id in user_data['req_ids']:
                StudentRequirement.objects.filter(id=req_id).update(
                    status='notified',
                    notified_at=timezone.now()
                )

            # Create notification record
            for req_id in user_data['req_ids']:
                RequirementNotification.objects.create(
                    student_requirement_id=req_id,
                    sent_by=request.user,
                    message=f"{message}\n\nMissing requirements: {req_names}"
                )

            # Create in-app bell notification
            from students_app.models import Notification, StudentInboxMessage
            Notification.objects.create(
                user=user,
                notification_type='general',
                title='Action Required: Missing Requirements',
                message=f"{message}\n\nMissing: {req_names}",
            )

            # Create inbox message so student sees it in their Inbox tab
            StudentInboxMessage.objects.create(
                user=user,
                subject='Action Required: Missing Admission Requirements',
                body=f"{message}\n\nMissing requirements: {req_names}\n\nPlease submit the required documents as soon as possible.",
                sent_by=request.user,
            )

            notifications_sent += 1

            # Send email notification (non-critical — in-app already created above)
            try:
                full_name = user.get_full_name() or user.email
                email_message = f"""Dear {full_name},

{message}

Missing Requirements:
- {req_names}

Please submit the required documents as soon as possible.

Best regards,
Admissions Office
"""
                send_mail(
                    subject='Action Required: Missing Admission Requirements',
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Failed to send email to {user.email}: {e}")

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            notes=f"Sent {notifications_sent} requirement notifications to students."
        )

        return JsonResponse({
            'success': True,
            'message': f'Notifications sent to {notifications_sent} student(s).'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_all_students(request):
    """Get list of all students with applications for selection."""
    from django.contrib.auth.models import User
    from students_app.models import PersonalDetails

    users = User.objects.filter(
        application__isnull=False
    ).select_related('application').distinct().order_by('username')

    data = []
    for user in users:
        # Get personal details if available
        personal = PersonalDetails.objects.filter(user=user).first()
        full_name = personal.first_name + ' ' + \
            personal.last_name if personal else user.get_full_name() or user.email

        app = Application.objects.filter(user=user).first()

        data.append({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': full_name,
            'application_id': app.application_id if app else None,
            'program': app.program if app else None
        })

    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def students_with_status(request):
    """
    Students with application + fields used by the admin Student Messaging UI
    (document progress, COR, grades) for filtering and counts.
    """
    from collections import defaultdict
    from decimal import Decimal
    from students_app.models import (
        CORSubmission,
        Document,
        GradeEntry,
        GradeSubmission,
        PersonalDetails,
    )

    # Get required count from CMS (source of truth for what documents are required).
    # Document.DOCUMENT_TYPE_CHOICES keys ('tor', 'deans_recommendation', …) do NOT
    # match the document_type values stored in the DB, which are CMS title strings
    # (e.g. 'Transcript of Records').  Using the model choices for the intersection
    # always produces an empty set, making every student appear to have 0 verified docs.
    try:
        from admin_app.models import CMSSettings
        cms_reqs = CMSSettings.objects.get_or_create(pk=1)[0].admission_requirements or []
        required_n = len(cms_reqs) or len(Document.DOCUMENT_TYPE_CHOICES)
    except Exception:
        required_n = len(Document.DOCUMENT_TYPE_CHOICES)

    users = (
        User.objects.filter(application__isnull=False)
        .select_related('application')
        .order_by('username')
    )
    user_ids = [u.id for u in users]

    # Count verified documents per user by document_type title (as stored in the DB).
    verified_doc_counts = defaultdict(int)
    for ver in (
        DocumentVerification.objects.filter(document__user_id__in=user_ids)
        .select_related('document')
    ):
        if ver.status == 'verified' and ver.document_id:
            verified_doc_counts[ver.document.user_id] += 1

    cor_latest = {}
    for row in (
        CORSubmission.objects.filter(user_id__in=user_ids)
        .order_by('user_id', '-uploaded_at')
    ):
        if row.user_id not in cor_latest:
            cor_latest[row.user_id] = row

    grade_latest = {}
    for row in (
        GradeSubmission.objects.filter(user_id__in=user_ids)
        .order_by('user_id', '-uploaded_at')
    ):
        if row.user_id not in grade_latest:
            grade_latest[row.user_id] = row

    submission_ids = [s.id for s in grade_latest.values()]
    failing_by_sub = defaultdict(int)
    if submission_ids:
        for entry in GradeEntry.objects.filter(submission_id__in=submission_ids):
            g = entry.grade
            if g is not None and g > Decimal('2.00'):
                failing_by_sub[entry.submission_id] += 1

    students = []
    for user in users:
        personal = PersonalDetails.objects.filter(user=user).first()
        if personal:
            full_name = f'{personal.first_name} {personal.last_name}'.strip()
        else:
            full_name = user.get_full_name() or user.email

        app = user.application
        documents_uploaded = verified_doc_counts[user.id]
        pending_documents = max(0, required_n - documents_uploaded)

        cor = cor_latest.get(user.id)
        cor_uploaded = bool(cor and cor.status == 'Verified')

        gs = grade_latest.get(user.id)
        failing_grades = failing_by_sub.get(gs.id, 0) if gs else 0
        gwa = None
        if gs and gs.gpa is not None:
            gwa = float(gs.gpa)

        students.append({
            'id': user.id,
            'full_name': full_name,
            'student_id': app.application_id if app else user.username,
            'documents_uploaded': documents_uploaded,
            'documents_required': required_n,
            'pending_documents': pending_documents,
            'cor_uploaded': cor_uploaded,
            'failing_grades': failing_grades,
            'gwa': gwa,
        })

    return JsonResponse({'success': True, 'students': students})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def send_admin_messaging(request):
    """
    Deliver admin outreach by channel:
    - notification: short bell items (students_app.Notification).
    - inbox: formal messages in the student portal Inbox (StudentInboxMessage).
    """
    from django.db import transaction
    from students_app.models import Notification, StudentInboxMessage

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)

    raw_ids = data.get('recipients') or data.get('user_ids') or []
    if not isinstance(raw_ids, list) or not raw_ids:
        return JsonResponse(
            {'success': False, 'message': 'recipients must be a non-empty list of user ids.'},
            status=400,
        )

    subject = (data.get('subject') or '').strip()
    body = (data.get('body') or '').strip()
    if not subject or not body:
        return JsonResponse(
            {'success': False, 'message': 'subject and body are required.'},
            status=400,
        )

    channel = (data.get('channel') or 'notification').strip().lower()
    if channel not in ('notification', 'inbox'):
        channel = 'notification'

    try:
        user_ids = [int(x) for x in raw_ids]
    except (TypeError, ValueError):
        return JsonResponse({'success': False, 'message': 'Invalid user id in recipients.'}, status=400)

    user_ids = list(dict.fromkeys(user_ids))
    if len(user_ids) > 2000:
        return JsonResponse(
            {'success': False, 'message': 'Too many recipients in one request (max 2000).'},
            status=400,
        )

    existing = set(
        User.objects.filter(id__in=user_ids, application__isnull=False).values_list(
            'id', flat=True
        )
    )
    target_ids = [uid for uid in user_ids if uid in existing]
    if not target_ids:
        return JsonResponse(
            {'success': False, 'message': 'No matching student accounts for the given ids.'},
            status=400,
        )

    title = subject[:255]
    message = body

    with transaction.atomic():
        if channel == 'inbox':
            StudentInboxMessage.objects.bulk_create(
                [
                    StudentInboxMessage(
                        user_id=uid,
                        subject=title[:255],
                        body=message,
                        sent_by=request.user,
                    )
                    for uid in target_ids
                ]
            )
        else:
            Notification.objects.bulk_create(
                [
                    Notification(
                        user_id=uid,
                        notification_type='general',
                        title=title[:255],
                        message=message,
                    )
                    for uid in target_ids
                ]
            )

    template_type = (data.get('type') or '').strip()
    AdminActivityLog.objects.create(
        admin=request.user,
        action='messaging',
        application=None,
        notes=(
            f"Messaging ({channel}): {len(target_ids)} student(s). "
            f"Subject: {subject[:120]!r}. Template: {template_type or 'custom'}."
        ),
    )

    return JsonResponse({'success': True, 'sent_count': len(target_ids)})


# ============== Program CMS APIs ==============

@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def list_cms_programs(request):
    """Return the CMSSettings.programs JSON list."""
    from ..models import CMSSettings
    try:
        cms, _ = CMSSettings.objects.get_or_create(pk=1)
        return JsonResponse({'success': True, 'programs': cms.programs or []})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_program_cms(request):
    """Get all program CMS data."""
    from ..models import CMSSettings, Faculty

    try:
        cms = CMSSettings.objects.get(pk=1)
    except CMSSettings.DoesNotExist:
        CMSSettings.objects.create(pk=1)
        cms = CMSSettings.objects.get(pk=1)

    # Get faculty members
    faculty_list = Faculty.objects.filter(is_active=True).order_by('order')
    faculties = [{
        'id': f.id,
        'first_name': f.first_name,
        'last_name': f.last_name,
        'title': f.title,
        'specializations': f.specializations,
        'photo': f.photo.url if f.photo else None,
        'order': f.order,
    } for f in faculty_list]

    data = {
        'program_name': cms.program_name,
        'program_degree': cms.program_degree,
        'program_title': cms.program_title,
        'program_tagline': cms.program_tagline,
        'program_description': cms.program_description,
        'program_institution': cms.program_institution,
        'program_copc_number': cms.program_copc_number,
        'program_effective_year': cms.program_effective_year,
        'program_accreditor': cms.program_accreditor,
        'program_objectives': cms.program_objectives,
        'program_outcomes': cms.program_outcomes,
        'program_curriculum': cms.program_curriculum,
        'program_stats': cms.program_stats,
        'faculties': faculties,
    }

    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_program_cms(request):
    """Update program CMS settings."""
    from ..models import CMSSettings

    try:
        data = json.loads(request.body)

        # Get or create CMS settings
        try:
            cms = CMSSettings.objects.get(pk=1)
        except CMSSettings.DoesNotExist:
            CMSSettings.objects.create(pk=1)
            cms = CMSSettings.objects.get(pk=1)

        # Update program basic info
        cms.program_name = data.get('program_name', cms.program_name).strip()
        cms.program_degree = data.get(
            'program_degree', cms.program_degree).strip()
        cms.program_title = data.get(
            'program_title', cms.program_title).strip()
        cms.program_tagline = data.get(
            'program_tagline', cms.program_tagline).strip()
        cms.program_description = data.get(
            'program_description', cms.program_description).strip()
        cms.program_institution = data.get(
            'program_institution', cms.program_institution).strip()
        cms.program_copc_number = data.get(
            'program_copc_number', cms.program_copc_number).strip()
        cms.program_effective_year = data.get(
            'program_effective_year', cms.program_effective_year).strip()
        cms.program_accreditor = data.get(
            'program_accreditor', cms.program_accreditor).strip()

        # Update objectives [{title, description}]
        objectives = data.get('program_objectives', None)
        if objectives is not None:
            cleaned_objectives = []
            for obj in objectives:
                title = str(obj.get('title', '')).strip()
                description = str(obj.get('description', '')).strip()
                if title:
                    cleaned_objectives.append(
                        {'title': title, 'description': description})
            cms.program_objectives = cleaned_objectives

        # Update outcomes [{number, title, description}]
        outcomes = data.get('program_outcomes', None)
        if outcomes is not None:
            cleaned_outcomes = []
            for outcome in outcomes:
                try:
                    number = int(outcome.get('number', 0))
                except (ValueError, TypeError):
                    number = 0
                title = str(outcome.get('title', '')).strip()
                description = str(outcome.get('description', '')).strip()
                if title and number > 0:
                    cleaned_outcomes.append({
                        'number': number,
                        'title': title,
                        'description': description
                    })
            cms.program_outcomes = cleaned_outcomes

        # Update curriculum [{title, courses: [{code, name, units}]}]
        curriculum = data.get('program_curriculum', None)
        if curriculum is not None:
            cleaned_curriculum = []
            for group in curriculum:
                if not isinstance(group, dict):
                    continue
                group_title = str(group.get('title', '')).strip()
                courses_raw = group.get('courses', []) or []
                if not isinstance(courses_raw, list):
                    courses_raw = []
                cleaned_courses = []
                for course in courses_raw:
                    if not isinstance(course, dict):
                        continue
                    code = str(course.get('code', '')).strip()
                    name = str(course.get('name', '')).strip()
                    try:
                        units = int(course.get('units', 0))
                    except (ValueError, TypeError):
                        units = 0
                    if code and name and units > 0:
                        cleaned_courses.append({
                            'code': code,
                            'name': name,
                            'units': units
                        })
                # Keep titled groups even when empty so the About CMS structure
                # is not dropped on save (previously only groups with courses
                # were persisted, which could wipe the catalog).
                if group_title:
                    cleaned_curriculum.append({
                        'title': group_title,
                        'courses': cleaned_courses
                    })
            cms.program_curriculum = cleaned_curriculum

        # Update stats [{stat_label, stat_value}]
        stats = data.get('program_stats', None)
        if stats is not None:
            cleaned_stats = []
            for stat in stats:
                label = str(stat.get('stat_label', '')).strip()
                value = str(stat.get('stat_value', '')).strip()
                if label and value:
                    cleaned_stats.append({
                        'stat_label': label,
                        'stat_value': value
                    })
            cms.program_stats = cleaned_stats

        cms.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Program CMS settings updated.'
        )

        return JsonResponse({'success': True, 'message': 'Program CMS settings updated successfully.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_faculty_list(request):
    """Get list of all faculty members."""
    from ..models import Faculty

    faculty = Faculty.objects.filter(is_active=True).order_by('order')
    data = [{
        'id': f.id,
        'first_name': f.first_name,
        'last_name': f.last_name,
        'title': f.title,
        'specializations': f.specializations,
        'photo': f.photo.url if f.photo else None,
        'order': f.order,
    } for f in faculty]

    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def add_faculty_member(request):
    """Add a new faculty member."""
    from ..models import Faculty

    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        title = request.POST.get('title', '').strip()
        specializations = request.POST.get('specializations', '').strip()
        photo = request.FILES.get('photo', None)

        if not first_name or not last_name or not title:
            return JsonResponse({
                'success': False,
                'message': 'First name, last name, and title are required.'
            }, status=400)

        # Validate photo if provided
        if photo:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if photo.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': 'Only JPG, PNG, and WEBP images are allowed.'
                }, status=400)

            max_size = 5 * 1024 * 1024  # 5MB
            if photo.size > max_size:
                return JsonResponse({
                    'success': False,
                    'message': 'Photo size must not exceed 5MB.'
                }, status=400)

        # Get next order number
        last_faculty = Faculty.objects.order_by('-order').first()
        next_order = (last_faculty.order + 1) if last_faculty else 1

        faculty = Faculty.objects.create(
            first_name=first_name,
            last_name=last_name,
            title=title,
            specializations=specializations,
            photo=photo if photo else None,
            order=next_order
        )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f"Added faculty member: {first_name} {last_name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty member added successfully.',
            'data': {
                'id': faculty.id,
                'first_name': faculty.first_name,
                'last_name': faculty.last_name,
                'title': faculty.title,
                'specializations': faculty.specializations,
                'photo': faculty.photo.url if faculty.photo else None,
                'order': faculty.order,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_faculty_member(request):
    """Update an existing faculty member."""
    from ..models import Faculty

    try:
        faculty_id = request.POST.get('faculty_id')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        title = request.POST.get('title', '').strip()
        specializations = request.POST.get('specializations', '').strip()
        photo = request.FILES.get('photo', None)

        if not faculty_id:
            return JsonResponse({
                'success': False,
                'message': 'Faculty ID is required.'
            }, status=400)

        faculty = Faculty.objects.get(id=faculty_id)

        # Update fields if provided
        if first_name:
            faculty.first_name = first_name
        if last_name:
            faculty.last_name = last_name
        if title:
            faculty.title = title

        faculty.specializations = specializations

        # Update photo if provided
        if photo:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if photo.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': 'Only JPG, PNG, and WEBP images are allowed.'
                }, status=400)

            max_size = 5 * 1024 * 1024  # 5MB
            if photo.size > max_size:
                return JsonResponse({
                    'success': False,
                    'message': 'Photo size must not exceed 5MB.'
                }, status=400)

            # Delete old photo if exists
            if faculty.photo:
                if default_storage.exists(faculty.photo.name):
                    default_storage.delete(faculty.photo.name)

            faculty.photo = photo

        faculty.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f"Updated faculty member: {faculty.first_name} {faculty.last_name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty member updated successfully.',
            'data': {
                'id': faculty.id,
                'first_name': faculty.first_name,
                'last_name': faculty.last_name,
                'title': faculty.title,
                'specializations': faculty.specializations,
                'photo': faculty.photo.url if faculty.photo else None,
                'order': faculty.order,
            }
        })
    except Faculty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Faculty member not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_faculty_member(request):
    """Delete a faculty member."""
    from ..models import Faculty

    try:
        data = json.loads(request.body)
        faculty_id = data.get('faculty_id')

        if not faculty_id:
            return JsonResponse({
                'success': False,
                'message': 'Faculty ID is required.'
            }, status=400)

        faculty = Faculty.objects.get(id=faculty_id)
        full_name = faculty.get_full_name()

        # Delete photo if exists
        if faculty.photo:
            if default_storage.exists(faculty.photo.name):
                default_storage.delete(faculty.photo.name)

        faculty.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f"Deleted faculty member: {full_name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty member deleted successfully.'
        })
    except Faculty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Faculty member not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reorder_faculty(request):
    """Reorder faculty members."""
    from ..models import Faculty

    try:
        data = json.loads(request.body)
        faculty_orders = data.get('faculty_orders', [])

        for item in faculty_orders:
            faculty_id = item.get('id')
            order = item.get('order')

            try:
                faculty = Faculty.objects.get(id=faculty_id)
                faculty.order = order
                faculty.save()
            except Faculty.DoesNotExist:
                continue

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Reordered faculty members.'
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty members reordered successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_messaging_history(request):
    """Return the last 20 admin outreach messages sent by this admin."""
    import re
    logs = (
        AdminActivityLog.objects.filter(
            admin=request.user,
            action='messaging',
        )
        .order_by('-timestamp')[:20]
    )
    history = []
    for log in logs:
        notes = log.notes or ''
        sent_count = 0
        subject = 'Message'
        channel = 'inbox'
        m = re.search(r'(\d+) student\(s\)', notes)
        if m:
            sent_count = int(m.group(1))
        m = re.search(r"Subject: '([^']*)'", notes)
        if m:
            subject = m.group(1)
        m = re.search(r'Messaging \((\w+)\)', notes)
        if m:
            channel = m.group(1)
        history.append({
            'subject': subject,
            'sent_count': sent_count,
            'channel': channel,
            'time': log.timestamp.strftime('%b %d, %Y · %I:%M %p'),
        })
    return JsonResponse({'success': True, 'history': history})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_student_replies(request):
    """Return student replies to admin inbox messages (newest first, unread first)."""
    from students_app.models import StudentMessageReply
    qs = (
        StudentMessageReply.objects
        .select_related('message', 'sent_by')
        .order_by('-created_at')[:100]
    )
    data = []
    for r in qs:
        pd = None
        try:
            from students_app.models import PersonalDetails
            pd = PersonalDetails.objects.filter(user=r.sent_by).first()
        except Exception:
            pass
        name = (
            f"{pd.first_name} {pd.last_name}".strip()
            if pd else r.sent_by.get_full_name() or r.sent_by.username
        )
        data.append({
            'id': r.id,
            'message_id': r.message_id,
            'subject': r.message.subject,
            'student_name': name,
            'student_email': r.sent_by.email,
            'body': r.body,
            'is_read': r.is_read_by_admin,
            'created_at': r.created_at.strftime('%b %d, %Y · %I:%M %p'),
        })
    unread = StudentMessageReply.objects.filter(is_read_by_admin=False).count()
    return JsonResponse({'success': True, 'replies': data, 'unread_count': unread})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def mark_student_replies_read(request):
    """Mark one or all student replies as read by admin."""
    from students_app.models import StudentMessageReply
    try:
        data = json.loads(request.body)
        reply_id = data.get('reply_id')
        if reply_id:
            StudentMessageReply.objects.filter(id=int(reply_id)).update(is_read_by_admin=True)
        else:
            StudentMessageReply.objects.filter(is_read_by_admin=False).update(is_read_by_admin=True)
        unread = StudentMessageReply.objects.filter(is_read_by_admin=False).count()
        return JsonResponse({'success': True, 'unread_count': unread})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admin_preferences(request):
    """Return the current admin's saved UI preferences."""
    try:
        profile, _ = AdminProfile.objects.get_or_create(user=request.user)
        return JsonResponse({'success': True, 'preferences': profile.preferences or {}})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(['POST'])
def save_admin_preferences(request):
    """Save admin UI preferences (academic_year, default_program, etc.)."""
    try:
        data = json.loads(request.body)
        profile, _ = AdminProfile.objects.get_or_create(user=request.user)
        profile.preferences = data
        profile.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ── Admin Notifications ────────────────────────────────────────────────────────

NOTIF_ICONS = {
    'cor_upload': 'file-text',
    'grade_upload': 'bar-chart-2',
    'requirement_submitted': 'check-square',
    'document_upload': 'upload-cloud',
}

NOTIF_COLORS = {
    'cor_upload': 'blue',
    'grade_upload': 'purple',
    'requirement_submitted': 'green',
    'document_upload': 'indigo',
}


def _notif_time_ago(dt):
    from django.utils import timezone as tz
    now = tz.now()
    diff = int((now - dt).total_seconds())
    if diff < 60:
        return 'Just now'
    if diff < 3600:
        return f"{diff // 60}m ago"
    if diff < 86400:
        return f"{diff // 3600}h ago"
    if diff < 604800:
        return f"{diff // 86400}d ago"
    return dt.strftime('%b %d, %Y')


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_admin_notifications(request):
    """Return paginated admin notifications, newest first."""
    page = int(request.GET.get('page', 1))
    page_size = 20
    offset = (page - 1) * page_size

    qs = AdminNotification.objects.select_related('student').order_by('-created_at')
    total = qs.count()
    unread_count = qs.filter(is_read=False).count()
    notifications = qs[offset: offset + page_size]

    data = []
    for n in notifications:
        student_name = n.student.get_full_name() or n.student.username
        data.append({
            'id': n.pk,
            'type': n.notification_type,
            'icon': NOTIF_ICONS.get(n.notification_type, 'bell'),
            'color': NOTIF_COLORS.get(n.notification_type, 'gray'),
            'title': n.title,
            'message': n.message,
            'student': student_name,
            'time': _notif_time_ago(n.created_at),
            'fullTime': n.created_at.strftime('%b %d, %Y · %I:%M %p'),
            'epoch': int(n.created_at.timestamp() * 1000),
            'is_read': n.is_read,
        })

    return JsonResponse({
        'notifications': data,
        'unread_count': unread_count,
        'total': total,
        'page': page,
        'has_more': (offset + page_size) < total,
    })


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def mark_admin_notifications_read(request):
    """Mark one notification (by id) or all notifications as read."""
    try:
        body = json.loads(request.body) if request.body else {}
        notif_id = body.get('id')
        if notif_id:
            AdminNotification.objects.filter(pk=notif_id).update(is_read=True)
        else:
            AdminNotification.objects.filter(is_read=False).update(is_read=True)
        unread = AdminNotification.objects.filter(is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_admin_notification_count(request):
    """Lightweight endpoint — returns only the unread count for badge polling."""
    count = AdminNotification.objects.filter(is_read=False).count()
    return JsonResponse({'unread_count': count})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_activity_log_api(request):
    """
    Return activity log entries with optional filtering and search.
    Query params:
      limit  (int, default 200)
      action (str) — raw action key, e.g. 'verified', 'rejected'
      search (str) — searches admin username, application ID, document type, notes
    """
    try:
        limit = min(int(request.GET.get('limit', 200)), 500)
        action = request.GET.get('action', '').strip()
        search = request.GET.get('search', '').strip()

        qs = AdminActivityLog.objects.select_related(
            'admin', 'application', 'document'
        ).order_by('-timestamp')

        if action:
            qs = qs.filter(action=action)

        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(admin__username__icontains=search) |
                Q(application__application_id__icontains=search) |
                Q(document__document_type__icontains=search) |
                Q(notes__icontains=search)
            )

        qs = qs[:limit]

        data = [
            {
                'time': log.timestamp.strftime('%Y-%m-%d %H:%M'),
                'admin': log.admin.username if log.admin else 'Unknown',
                'appId': log.application.application_id if log.application else 'N/A',
                'doc': log.document.document_type if log.document else 'General',
                'action': log.get_action_display(),
                'actionKey': log.action,
                'notes': log.notes,
            }
            for log in qs
        ]

        return JsonResponse({'success': True, 'data': data, 'total': len(data)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def save_program(request):
    """Create or update a program entry in CMSSettings.programs JSON list."""
    from ..models import CMSSettings
    try:
        data = json.loads(request.body)
        program_id = data.get('id')
        if not program_id or not data.get('name', '').strip():
            return JsonResponse({'success': False, 'message': 'id and name are required.'}, status=400)

        cms, _ = CMSSettings.objects.get_or_create(pk=1)
        programs = list(cms.programs or [])

        # Build the cleaned program object preserving all fields the frontend sends
        allowed_fields = [
            'id', 'name', 'degree', 'level', 'dept', 'institution', 'copc',
            'eff_year', 'accreditor', 'hero_badge', 'hero_tagline', 'description',
            'ched_title', 'ched_body', 'slug', 'order', 'visible', 'logo',
            'college_logo', 'college',
            'stats', 'curriculum', 'outcomes', 'objectives', 'faculty', 'program_heads',
            'curriculum_eyebrow', 'curriculum_title', 'curriculum_title_italic', 'curriculum_subtitle',
            'outcomes_eyebrow', 'outcomes_title', 'outcomes_title_italic', 'outcomes_subtitle',
            'objectives_eyebrow', 'objectives_title', 'objectives_title_italic', 'objectives_subtitle',
            'faculty_eyebrow', 'faculty_title', 'faculty_title_italic', 'faculty_subtitle',
        ]
        program_obj = {k: data[k] for k in allowed_fields if k in data}
        program_obj['name'] = program_obj.get('name', '').strip()
        # Auto-generate slug from name if not provided
        if not program_obj.get('slug'):
            import re
            program_obj['slug'] = re.sub(r'[^a-z0-9]+', '-', program_obj['name'].lower()).strip('-')

        idx = next((i for i, p in enumerate(programs) if p.get('id') == program_id), None)
        if idx is not None:
            # Preserve the original creator on updates
            existing_created_by = programs[idx].get('created_by')
            programs[idx] = program_obj
            if existing_created_by is not None:
                programs[idx]['created_by'] = existing_created_by
        else:
            # Enforce one-program-per-user rule
            user_id = request.user.id
            if any(p.get('created_by') == user_id for p in programs):
                return JsonResponse(
                    {'success': False, 'message': 'You already have a program. Delete it first before creating a new one.'},
                    status=403,
                )
            program_obj['created_by'] = user_id
            programs.append(program_obj)

        cms.programs = programs
        cms.save(update_fields=['programs'])

        # Keep Program DB record in sync (anchors prospectus/curriculum)
        prog_slug = program_obj.get('slug') or ''
        if prog_slug:
            Program.objects.update_or_create(
                slug=prog_slug,
                defaults={
                    'name': program_obj['name'],
                    'program_label': program_obj.get('degree', ''),
                },
            )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f'Program {"updated" if idx is not None else "created"}: {program_obj["name"]}',
        )
        return JsonResponse({'success': True, 'program': program_obj})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_program(request):
    """Remove a program entry from CMSSettings.programs by id."""
    from ..models import CMSSettings
    try:
        data = json.loads(request.body)
        program_id = data.get('id')
        if not program_id:
            return JsonResponse({'success': False, 'message': 'id is required.'}, status=400)

        cms, _ = CMSSettings.objects.get_or_create(pk=1)
        programs = list(cms.programs or [])
        original_len = len(programs)
        deleted_prog = next((p for p in programs if p.get('id') == program_id), None)
        programs = [p for p in programs if p.get('id') != program_id]
        cms.programs = programs
        cms.save(update_fields=['programs'])

        # Remove Program DB record (cascades to all prospectuses/curriculum)
        if deleted_prog and deleted_prog.get('slug'):
            Program.objects.filter(slug=deleted_prog['slug']).delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f'Program deleted (id={program_id})',
        )
        return JsonResponse({'success': True, 'deleted': original_len - len(programs)})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
