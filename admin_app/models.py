from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from students_app.models import Document


class Application(models.Model):
    """
    Represents a student's application for a graduate program.
    Links a user to their application and tracks submission status.
    """
    PROGRAM_CHOICES = [
        ('MIT', 'Master of Information Technology'),
        ('MBA', 'Master of Business Administration'),
        ('MPA', 'Master of Public Administration'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('verified', 'Verified'),
        ('incomplete', 'Incomplete'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='application')
    program = models.CharField(max_length=50, choices=PROGRAM_CHOICES, default='MIT')
    application_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submission_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submission_date']

    def __str__(self):
        return f"{self.application_id} - {self.user.email} ({self.program})"

    def get_full_name(self):
        """Get student's full name from PersonalDetails if available."""
        from students_app.models import PersonalDetails
        try:
            personal = PersonalDetails.objects.get(user=self.user)
            return f"{personal.first_name} {personal.last_name}"
        except PersonalDetails.DoesNotExist:
            return self.user.get_full_name() or self.user.email

    def get_contact_number(self):
        """Get student's contact number from PersonalDetails if available."""
        from students_app.models import PersonalDetails
        try:
            personal = PersonalDetails.objects.get(user=self.user)
            return personal.contact_number
        except PersonalDetails.DoesNotExist:
            return 'N/A'

    def count_documents(self):
        """Count total documents submitted for this application."""
        return Document.objects.filter(user=self.user).count()

    def get_document_status_summary(self):
        """Get summary of document verification statuses."""
        verifications = DocumentVerification.objects.filter(
            document__user=self.user
        ).values('status').annotate(count=models.Count('id'))
        return {v['status']: v['count'] for v in verifications}


class DocumentVerification(models.Model):
    """
    Tracks the verification status of individual documents.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('reviewing', 'Under Review'),
        ('verified', 'Verified'),
        ('incomplete', 'Incomplete'),
        ('rejected', 'Rejected'),
    ]
    
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='verification')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.document.document_type} - {self.status}"


class AdminActivityLog(models.Model):
    """
    Logs all admin actions for audit trail and activity history.
    """
    ACTION_CHOICES = [
        ('verified', 'Verified Document'),
        ('rejected', 'Rejected Document'),
        ('incomplete', 'Marked Incomplete'),
        ('resubmit', 'Requested Resubmission'),
        ('note', 'Added Note'),
        ('comment', 'Added Comment'),
    ]
    
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_activities')
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='activity_logs')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'

    def __str__(self):
        return f"{self.admin.username if self.admin else 'Unknown'} - {self.action} on {self.application.application_id}"
