from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import DocumentVerification, AdminNotification, StudentRequirement
from students_app.models import Notification, CORSubmission, GradeSubmission


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
    previous_status = getattr(instance, '_previous_status', None)

    # Skip saves where status did not actually change.
    if previous_status == instance.status:
        return

    # Skip implicit first-save pending entries created by get_or_create.
    if created and instance.status == 'pending':
        return

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

    Notification.objects.create(
        user=student,
        notification_type=config['type'],
        title=config['title'],
        message=message,
    )


@receiver(pre_save, sender=DocumentVerification)
def capture_previous_document_status(sender, instance, **kwargs):
    """
    Attach previous status so post_save can determine real transitions.
    """
    if not instance.pk:
        instance._previous_status = None
        return

    instance._previous_status = (
        sender.objects.filter(pk=instance.pk)
        .values_list('status', flat=True)
        .first()
    )


# ── Admin notifications triggered by student uploads ──────────────────────────

@receiver(post_save, sender=CORSubmission)
def notify_admin_cor_upload(sender, instance, created, **kwargs):
    """Create an AdminNotification whenever a student uploads a new COR."""
    if not created:
        return
    student = instance.user
    full_name = student.get_full_name() or student.username
    AdminNotification.objects.create(
        notification_type='cor_upload',
        student=student,
        title='COR Uploaded',
        message=f"{full_name} uploaded a Certificate of Registration for {instance.school_year}, Semester {instance.semester}.",
        related_object_id=instance.pk,
    )


@receiver(post_save, sender=GradeSubmission)
def notify_admin_grade_upload(sender, instance, created, **kwargs):
    """Create an AdminNotification whenever a student uploads a grade screenshot."""
    if not created:
        return
    student = instance.user
    full_name = student.get_full_name() or student.username
    AdminNotification.objects.create(
        notification_type='grade_upload',
        student=student,
        title='Grade Screenshot Uploaded',
        message=f"{full_name} submitted grades for {instance.curriculum_name} — {instance.school_year}, Semester {instance.semester}.",
        related_object_id=instance.pk,
    )


@receiver(pre_save, sender=StudentRequirement)
def capture_previous_requirement_status(sender, instance, **kwargs):
    """Attach previous status so post_save can detect the submitted transition."""
    if not instance.pk:
        instance._prev_req_status = None
        return
    instance._prev_req_status = (
        sender.objects.filter(pk=instance.pk)
        .values_list('status', flat=True)
        .first()
    )


@receiver(post_save, sender=StudentRequirement)
def notify_admin_requirement_submitted(sender, instance, created, **kwargs):
    """Create an AdminNotification when a student marks a requirement as submitted."""
    if instance.status != 'submitted':
        return
    prev = getattr(instance, '_prev_req_status', None)
    if prev == 'submitted':
        return
    student = instance.user
    full_name = student.get_full_name() or student.username
    req_name = instance.requirement.name if instance.requirement else 'requirement'
    AdminNotification.objects.create(
        notification_type='requirement_submitted',
        student=student,
        title='Requirement Submitted',
        message=f"{full_name} submitted the requirement: {req_name}.",
        related_object_id=instance.pk,
    )