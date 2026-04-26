"""
Utility functions for admin dashboard to fetch and process data.
"""
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Application, DocumentVerification, AdminActivityLog
from students_app.models import Document, PersonalDetails


def get_applications_summary():
    """
    Get summary statistics of all applications.
    Returns: dict with counts for each status
    """
    summary = {
        'total': Application.objects.count(),
        'pending': Application.objects.filter(status='pending').count(),
        'reviewing': Application.objects.filter(status='reviewing').count(),
        'verified': Application.objects.filter(status='verified').count(),
        'incomplete': Application.objects.filter(status='incomplete').count(),
        'rejected': Application.objects.filter(status='rejected').count(),
    }
    return summary


def get_all_applications():
    """
    Get all applications with related document data.
    Returns: QuerySet of Applications with prefetch
    """
    return Application.objects.select_related('user').prefetch_related(
        'user__document_set',
        'user__document_set__verification'
    ).order_by('-submission_date')


def get_application_details(application_id):
    """
    Get detailed information about a specific application.
    """
    try:
        app = Application.objects.select_related(
            'user').get(application_id=application_id)
        return {
            'id': app.application_id,
            'name': app.get_full_name(),
            'email': app.user.email,
            'mobile': app.get_contact_number(),
            'course': app.program,
            'status': app.status,
            'submission_date': app.submission_date.strftime('%Y-%m-%d'),
            'last_activity': app.last_activity.strftime('%Y-%m-%d'),
            'remarks': app.remarks,
            'documents': get_application_documents(app.user),
        }
    except Application.DoesNotExist:
        return None


def get_application_documents(user):
    """
    Get all documents for a user with their verification status.
    Returns: list of document dicts
    """
    documents = []
    for doc in Document.objects.filter(user=user).select_related('verification'):
        try:
            verification = doc.verification
            status = verification.status
            verified_by = verification.verified_by.username if verification.verified_by else ''
            verified_on = verification.verified_at.strftime(
                '%Y-%m-%d') if verification.verified_at else ''
            issues = [
                verification.rejection_reason] if verification.rejection_reason else []
        except DocumentVerification.DoesNotExist:
            status = 'pending'
            verified_by = ''
            verified_on = ''
            issues = []

        documents.append({
            'id': doc.id,
            'name': doc.get_document_type_display(),
            'type': 'Academic Form',
            'status': status,
            'uploadDate': doc.uploaded_at.strftime('%Y-%m-%d'),
            'verifiedBy': verified_by,
            'verifiedOn': verified_on,
            'issues': issues,
            'file_name': doc.file_name,
        })

    return documents


def get_recent_applications(limit=5):
    """
    Get recent applications for dashboard display.
    """
    apps = Application.objects.select_related(
        'user').order_by('-submission_date')[:limit]
    return [
        {
            'id': app.application_id,
            'name': app.get_full_name(),
            'course': app.program,
            'status': app.status,
            'submission_date': app.submission_date.strftime('%Y-%m-%d'),
        }
        for app in apps
    ]


def get_verification_progress():
    """
    Get verification progress across all applications.
    Returns stats about document verification.
    """
    doc_verifications = DocumentVerification.objects.values(
        'status').annotate(count=Count('id'))
    progress = {
        'verified': 0,
        'reviewing': 0,
        'pending': 0,
        'rejected': 0,
    }

    for item in doc_verifications:
        if item['status'] in progress:
            progress[item['status']] = item['count']

    total = sum(progress.values())

    return {
        'verified': progress.get('verified', 0),
        'reviewing': progress.get('reviewing', 0),
        'pending': progress.get('pending', 0),
        'rejected': progress.get('rejected', 0),
        'total': total,
    }


def get_activity_log(limit=20):
    """
    Get recent admin activity logs.
    """
    logs = AdminActivityLog.objects.select_related(
        'admin', 'application', 'document'
    ).order_by('-timestamp')[:limit]

    return [
        {
            'time': log.timestamp.strftime('%Y-%m-%d %H:%M'),
            'admin': log.admin.username if log.admin else 'Unknown',
            'appId': log.application.application_id if log.application else 'N/A',
            'doc': log.document.get_document_type_display() if log.document else 'General',
            'action': log.get_action_display(),
            'notes': log.notes,
        }
        for log in logs
    ]


def log_admin_activity(admin, application, action, document=None, notes=''):
    """
    Create an admin activity log entry.
    """
    return AdminActivityLog.objects.create(
        admin=admin,
        application=application,
        document=document,
        action=action,
        notes=notes,
    )


def update_document_verification(document, status, admin_user=None, remarks='', rejection_reason=''):
    """
    Update or create document verification record.
    """
    verification, created = DocumentVerification.objects.update_or_create(
        document=document,
        defaults={
            'status': status,
            'verified_by': admin_user if status == 'verified' else None,
            'verified_at': timezone.now() if status == 'verified' else None,
            'remarks': remarks,
            'rejection_reason': rejection_reason if status == 'rejected' else '',
        }
    )
    return verification


def get_document_type_display(doc_type):
    """
    Get human readable document type name.
    """
    type_map = {
        'deans_recommendation': "Dean's Recommendation",
        'tor': 'Transcript of Records',
        'honorable_dismissal': 'Honorable Dismissal',
        'psa': 'PSA (Live Birth)',
        'gsat': 'GSAT (Graduate School Admission Test)',
    }
    return type_map.get(doc_type, doc_type)
