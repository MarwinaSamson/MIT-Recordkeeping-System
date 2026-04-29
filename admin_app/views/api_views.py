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
        verification, created = DocumentVerification.objects.get_or_create(
            document=doc)
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
        verification, created = DocumentVerification.objects.get_or_create(
            document=doc)
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

        # Save admission details if provided (on verify)
        if 'semester' in data:
            app.semester = data.get('semester', '').strip()
        if 'year_admitted' in data:
            app.year_admitted = data.get('year_admitted', '').strip()
        if 'curriculum' in data:
            app.curriculum = data.get('curriculum', '').strip()

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
            'hero_tagline': data.get('hero_tagline', cms.hero_tagline).strip(),
            'application_deadline': data.get('application_deadline') or None,
        }

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

        # Validate and save downloads list [{name, url, file_type}]
        raw_downloads = data.get('downloads', None)
        if raw_downloads is not None:
            cleaned_downloads = []
            for d in raw_downloads:
                name = str(d.get('name', '')).strip()
                url = str(d.get('url', '')).strip()
                file_type = str(d.get('file_type', '')).strip()
                if name and url:
                    cleaned_downloads.append({
                        'name': name,
                        'url': url,
                        'file_type': file_type,
                    })
            update_data['downloads'] = cleaned_downloads

        # Use bulk update for better performance
        CMSSettings.objects.filter(pk=1).update(**update_data)

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Homepage CMS settings updated.'
        )

        return JsonResponse({'success': True, 'message': 'CMS settings saved.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def upload_cms_file(request):
    """Upload a file for CMS downloads section."""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided.'
            }, status=400)

        file = request.FILES['file']

        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'File size must not exceed 50MB.'
            }, status=400)

        # Save file to media/downloads
        from django.core.files.storage import default_storage
        file_path = f'downloads/{file.name}'
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
