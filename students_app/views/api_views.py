import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from admin_app.models import DocumentVerification, Application
from students_app.models import Document, Notification, PersonalDetails, PrivacyConsent


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
        submission_deadline = application.submission_deadline.strftime(
            '%B %d, %Y')
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
        verification = DocumentVerification.objects.filter(
            document=doc).first()

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
    notifications = Notification.objects.filter(
        user=request.user).order_by('-created_at')[:20]

    notif_list = []
    for notif in notifications:
        colors = NOTIFICATION_COLOR_MAP.get(
            notif.notification_type, NOTIFICATION_COLOR_MAP['general'])
        icon = NOTIFICATION_ICON_MAP.get(
            notif.notification_type, 'fa-info-circle')

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
    Notification.objects.filter(
        user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({
        'status': 'success',
        'unread_count': 0,
    })


@login_required
@require_http_methods(["POST"])
def submit_application(request):
    """
    Handle application submission from the review page.
    Creates/updates PersonalDetails and Application records in the database.
    Expects JSON payload with application data from the student form.
    """
    try:
        data = json.loads(request.body)
        user = request.user

        # Extract personal details from the submitted data
        personal_details_data = data.get('personalDetails', {})

        # Create or update PersonalDetails record
        personal_details_obj, created = PersonalDetails.objects.update_or_create(
            user=user,
            defaults={
                'first_name': personal_details_data.get('first_name', ''),
                'middle_name': personal_details_data.get('middle_name', ''),
                'last_name': personal_details_data.get('last_name', ''),
                'dob': personal_details_data.get('dob', ''),
                'age': personal_details_data.get('age', ''),
                'gender': personal_details_data.get('gender', ''),
                'civil_status': personal_details_data.get('civil_status', ''),
                'place_of_birth': personal_details_data.get('place_of_birth', ''),
                'religion': personal_details_data.get('religion', ''),
                'religion_other': personal_details_data.get('religion_other', ''),
                'ethnicity': personal_details_data.get('ethnicity', ''),
                'ethnicity_other': personal_details_data.get('ethnicity_other', ''),
                'nationality': personal_details_data.get('nationality', ''),
                'nationality_other': personal_details_data.get('nationality_other', ''),
                'disability': personal_details_data.get('disability', ''),
                'disability_other': personal_details_data.get('disability_other', ''),
                'permanent_address': personal_details_data.get('permanent_address', ''),
                'current_address': personal_details_data.get('current_address', ''),
                'contact_number': personal_details_data.get('contact_number', ''),
                'email': personal_details_data.get('email', ''),
                'name_of_parent': personal_details_data.get('name_of_parent', ''),
                'relationship': personal_details_data.get('relationship', ''),
                'parent_income': personal_details_data.get('parent_income', ''),
                'name_of_spouse': personal_details_data.get('name_of_spouse', ''),
                'spouse_contact_number': personal_details_data.get('spouse_contact_number', ''),
                'spouse_income': personal_details_data.get('spouse_income', ''),
            }
        )

        # Save privacy consent to DB
        privacy_data = data.get('privacyConsent', {})
        if privacy_data.get('agreed'):
            consent, _ = PrivacyConsent.objects.get_or_create(user=user)
            consent.agreed = True
            consent.name = privacy_data.get('name', '')
            consent.signed_at = timezone.now()
            consent.user_agent = privacy_data.get('userAgent', '')
            consent.ip_address = request.META.get('REMOTE_ADDR', '')
            consent.form_version = privacy_data.get('formVersion', '1.0')
            consent.save()

        # Check if application already exists
        existing_app = Application.objects.filter(user=user).first()

        # Generate the correct application ID based on user ID
        app_id = f"MIT-{str(user.id).zfill(4)}"

        if existing_app:
            # Update existing application with new format application ID
            existing_app.program = data.get(
                'educationalBackground', {}).get('program', '')
            existing_app.status = 'pending'
            existing_app.last_activity = timezone.now()
            existing_app.application_id = app_id  # Update to new format
            existing_app.save()
            application = existing_app
        else:
            # Create new application with generated ID based on user ID
            application = Application.objects.create(
                user=user,
                program=data.get('educationalBackground',
                                 {}).get('program', ''),
                application_id=app_id,
                status='pending',
                last_activity=timezone.now(),
            )

        return JsonResponse({
            'success': True,
            'message': 'Application submitted successfully',
            'application_id': application.application_id,
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data',
        }, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error submitting application: {str(e)}',
        }, status=500)
