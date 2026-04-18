"""
API views for admin dashboard actions.
Handles document verification, rejection, and application status updates.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
import json

from .models import Application, DocumentVerification, AdminActivityLog
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
