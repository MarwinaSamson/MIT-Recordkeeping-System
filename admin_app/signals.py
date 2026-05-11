from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DocumentVerification
from students_app.models import Notification


NOTIFICATION_CONFIG = {
    'verified': {
        'type':    'document_verified',
        'title':   'Document Verified ✓',
        'message': 'Your {doc_type} has been verified and approved by the admissions team.',
    },
    'rejected': {
        'type':    'document_rejected',
        'title':   'Document Rejected',
        'message': 'Your {doc_type} was rejected. {reason}Please re-upload a corrected copy.',
    },
    'reviewing': {
        'type':    'document_reviewing',
        'title':   'Document Under Review',
        'message': 'Your {doc_type} is now being reviewed by the admissions team.',
    },
    'incomplete': {
        'type':    'document_rejected',
        'title':   'Document Marked Incomplete',
        'message': 'Your {doc_type} was marked incomplete. {reason}Please re-upload a complete copy.',
    },
    'pending': {
        'type':    'general',
        'title':   'Document Received',
        'message': 'Your {doc_type} has been received and is awaiting review.',
    },
}


@receiver(post_save, sender=DocumentVerification)
def notify_student_on_status_change(sender, instance, created, **kwargs):
    """
    Fires every time a DocumentVerification record is saved.
    Creates a Notification for the student if the status changed.
    """
    student = instance.document.user
    if not student:
        return

    new_status = instance.status
    config     = NOTIFICATION_CONFIG.get(new_status)
    if not config:
        return

    doc_type      = instance.document.document_type or 'document'
    rejection_note = ''
    if instance.rejection_reason:
        rejection_note = f'Reason: {instance.rejection_reason}. '

    message = config['message'].format(
        doc_type=doc_type,
        reason=rejection_note,
    )

    # Avoid duplicate notifications: skip if the latest notification for
    # this document + status already exists (prevents double-saves firing twice)
    already_exists = Notification.objects.filter(
        user=student,
        notification_type=config['type'],
        title=config['title'],
        message=message,
    ).exists()

    if not already_exists:
        Notification.objects.create(
            user=student,
            notification_type=config['type'],
            title=config['title'],
            message=message,
        )