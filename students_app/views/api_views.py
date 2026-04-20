import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from admin_app.models import DocumentVerification, Application
from students_app.models import Document, Notification


DOCUMENT_TYPE_MAP = {
    'deans_recommendation': 'deansRec',
    'tor': 'tor',
    'honorable_dismissal': 'honorableDismissal',
    'psa': 'psa',
    'gsat': 'gsat',
}

STATUS_MAP = {
    'verified': 'approved',
    'reviewing': 'review',
    'rejected': 'rejected',
    'pending': 'pending',
    'incomplete': 'pending',
}


@login_required
@require_http_methods(["GET"])
def get_document_status(request):
    """
    Return current document verification statuses for the logged-in student.
    Used by polling mechanism on student dashboard.
    """
    # Count verified and reviewing documents
    verified_count = DocumentVerification.objects.filter(
        document__user=request.user, status='verified'
    ).count()
    reviewing_count = DocumentVerification.objects.filter(
        document__user=request.user, status='reviewing'
    ).count()
    rejected_count = DocumentVerification.objects.filter(
        document__user=request.user, status='rejected'
    ).count()
    total_documents = DocumentVerification.objects.filter(
        document__user=request.user
    ).count()
    
    # Calculate progress (approved documents out of total)
    progress_percent = 0
    if total_documents > 0:
        progress_percent = round((verified_count / total_documents) * 100)
    
    # Get application status and deadline
    application = Application.objects.filter(user=request.user).first()
    
    application_status = application.status if application else "pending"
    submission_deadline = ""
    if application and application.submission_deadline:
        submission_deadline = application.submission_deadline.strftime('%B %d, %Y')
    else:
        submission_deadline = "TBA"
    
    return JsonResponse({
        "verified_documents": verified_count,
        "reviewing_documents": reviewing_count,
        "rejected_documents": rejected_count,
        "total_documents": total_documents,
        "progress_percent": progress_percent,
        "application_status": application_status,
        "submission_deadline": submission_deadline,
    })


@login_required
@require_http_methods(["GET"])
def get_document_details(request):
    """
    Return detailed document verification statuses for all documents.
    Maps database statuses to frontend display format.
    """
    documents = Document.objects.filter(user=request.user)
    doc_statuses = {}
    
    for doc in documents:
        # Get the document key
        key = DOCUMENT_TYPE_MAP.get(doc.document_type)
        if not key:
            continue
        
        # Get verification status if it exists
        verification = DocumentVerification.objects.filter(document=doc).first()
        
        if verification:
            frontend_status = STATUS_MAP.get(verification.status, 'pending')
            doc_statuses[key] = {
                'status': frontend_status,
                'uploaded': True,
                'rejection_reason': verification.rejection_reason or '',
                'remarks': verification.remarks or '',
            }
        else:
            # Document uploaded but not yet verified
            doc_statuses[key] = {
                'status': 'pending',
                'uploaded': True,
                'rejection_reason': '',
                'remarks': '',
            }
    
    return JsonResponse(doc_statuses)


NOTIFICATION_ICON_MAP = {
    'document_verified': 'fa-check-circle',
    'document_rejected': 'fa-times-circle',
    'document_reviewing': 'fa-search',
    'application_status': 'fa-file',
    'deadline_reminder': 'fa-bell',
    'general': 'fa-info-circle',
}

NOTIFICATION_COLOR_MAP = {
    'document_verified': {'color': '#15803D', 'bg': '#F0FDF4'},  # Green
    'document_rejected': {'color': '#DC2626', 'bg': '#FEF2F2'},   # Red
    'document_reviewing': {'color': '#1D4ED8', 'bg': '#EFF6FF'},  # Blue
    'application_status': {'color': '#B45309', 'bg': '#FFFBEB'},  # Amber
    'deadline_reminder': {'color': '#B45309', 'bg': '#FFFBEB'},   # Amber
    'general': {'color': '#6B7280', 'bg': '#F9FAFB'},             # Gray
}


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    Return all notifications for the logged-in student.
    Includes styling information for frontend rendering.
    """
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    notif_list = []
    for notif in notifications:
        colors = NOTIFICATION_COLOR_MAP.get(notif.notification_type, NOTIFICATION_COLOR_MAP['general'])
        icon = NOTIFICATION_ICON_MAP.get(notif.notification_type, 'fa-info-circle')
        
        # Format timestamp (relative time)
        time_diff = (timezone.now() - notif.created_at).total_seconds()
        if time_diff < 60:
            time_str = "Just now"
        elif time_diff < 3600:
            mins = int(time_diff / 60)
            time_str = f"{mins} minute{'s' if mins > 1 else ''} ago"
        elif time_diff < 86400:
            hours = int(time_diff / 3600)
            time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif time_diff < 604800:
            days = int(time_diff / 86400)
            time_str = f"{days} day{'s' if days > 1 else ''} ago"
        else:
            time_str = notif.created_at.strftime("%b %d, %Y")
        
        notif_list.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'icon': icon,
            'color': colors['color'],
            'bg': colors['bg'],
            'time': time_str,
            'read': notif.is_read,
        })
    
    return JsonResponse({
        'notifications': notif_list,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    })


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    """
    Mark a notification as read.
    """
    try:
        data = json.loads(request.body)
        notif_id = data.get('notification_id')
        
        notification = Notification.objects.get(id=notif_id, user=request.user)
        notification.mark_as_read()
        
        return JsonResponse({
            'status': 'success',
            'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        })
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    Mark all notifications as read for the logged-in student.
    """
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({
        'status': 'success',
        'unread_count': 0,
    })


@login_required
@require_http_methods(["POST"])
def submit_application(request):
    """
    Submit application - creates Application record and related data in the database.
    Called from review page when student clicks "Submit Application".
    """
    try:
        from students_app.models import PersonalDetails
        import uuid
        
        data = json.loads(request.body)
        
        # Get or create PersonalDetails from the submitted data
        personal_data = data.get('personalDetails', {})
        
        personal, _ = PersonalDetails.objects.get_or_create(
            user=request.user,
            defaults={
                'first_name': personal_data.get('first_name', ''),
                'middle_name': personal_data.get('middle_name', ''),
                'last_name': personal_data.get('last_name', ''),
                'dob': personal_data.get('dob', None),
                'gender': personal_data.get('gender', ''),
                'civil_status': personal_data.get('civil_status', ''),
                'place_of_birth': personal_data.get('place_of_birth', ''),
                'religion': personal_data.get('religion', ''),
                'ethnicity': personal_data.get('ethnicity', ''),
                'nationality': personal_data.get('nationality', ''),
                'disability': personal_data.get('disability', ''),
                'permanent_address': personal_data.get('permanent_address', ''),
                'current_address': personal_data.get('current_address', ''),
                'contact_number': personal_data.get('contact_number', ''),
                'email': personal_data.get('email', request.user.email),
                'name_of_parent': personal_data.get('name_of_parent', ''),
                'relationship': personal_data.get('relationship', ''),
                'parent_income': personal_data.get('parent_income', ''),
                'name_of_spouse': personal_data.get('name_of_spouse', ''),
                'spouse_contact_number': personal_data.get('spouse_contact_number', ''),
                'spouse_income': personal_data.get('spouse_income', ''),
            }
        )
        
        # Update if it already exists
        if not _:
            personal.first_name = personal_data.get('first_name', personal.first_name)
            personal.middle_name = personal_data.get('middle_name', personal.middle_name)
            personal.last_name = personal_data.get('last_name', personal.last_name)
            personal.save()
        
        # Create or update Application record
        app_id = f"WMSU-GS-{uuid.uuid4().hex[:8].upper()}"
        application, created = Application.objects.get_or_create(
            user=request.user,
            defaults={
                'application_id': app_id,
                'program': 'MIT',  # Default program
                'status': 'pending',
            }
        )
        
        if not created:
            # Application already exists, just update status if needed
            if application.status == 'pending':
                application.status = 'reviewing'
                application.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Application submitted successfully',
            'application_id': application.application_id,
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error submitting application: {str(e)}'
        }, status=400)
