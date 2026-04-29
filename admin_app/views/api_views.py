"""
API views for admin dashboard actions.
Handles document verification, rejection, and application status updates.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.files.storage import default_storage
import json

from ..models import Application, DocumentVerification, AdminActivityLog, AdminProfile
from students_app.models import Document


def is_superuser(user):
    """Check if user is a superuser."""
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def verify_document(request):
    """Verify a document and update its status."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')
        
        # Get the application
        app = Application.objects.get(application_id=app_id)
        
        # Get the document
        doc = Document.objects.get(id=doc_id, user=app.user)
        
        # Get or create verification record
        verification, created = DocumentVerification.objects.get_or_create(document=doc)
        verification.status = 'verified'
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.save()
        
        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='verified',
            application=app,
            document=doc,
            notes=f"Document verified."
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Document {doc.file_name} marked as verified.',
            'status': 'verified'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reject_document(request):
    """Reject a document and record the reason."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')
        reason = data.get('reason', 'Document rejected.')
        
        # Get the application
        app = Application.objects.get(application_id=app_id)
        
        # Get the document
        doc = Document.objects.get(id=doc_id, user=app.user)
        
        # Get or create verification record
        verification, created = DocumentVerification.objects.get_or_create(document=doc)
        verification.status = 'rejected'
        verification.rejection_reason = reason
        verification.save()
        
        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='rejected',
            application=app,
            document=doc,
            notes=f"Document rejected: {reason}"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Document {doc.file_name} marked as rejected.',
            'status': 'rejected'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reset_document_verification(request):
    """Reset document verification status back to pending/under review."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')
        
        # Get the application
        app = Application.objects.get(application_id=app_id)
        
        # Get the document
        doc = Document.objects.get(id=doc_id, user=app.user)
        
        # Get verification record
        try:
            verification = DocumentVerification.objects.get(document=doc)
            old_status = verification.status
            verification.status = 'reviewing'
            verification.verified_by = None
            verification.verified_at = None
            verification.rejection_reason = ''
            verification.save()
            
            # Log the activity
            AdminActivityLog.objects.create(
                admin=request.user,
                action='resubmit',
                application=app,
                document=doc,
                notes=f"Document verification reset from {old_status} to reviewing."
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Document {doc.file_name} verification reset.',
                'status': 'reviewing'
            })
        except DocumentVerification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No verification record found for this document.'
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


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
        admin_profile, created = AdminProfile.objects.get_or_create(user=request.user)
        
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
