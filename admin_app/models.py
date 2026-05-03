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

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='application')
    program = models.CharField(
        max_length=50, choices=PROGRAM_CHOICES, default='MIT')
    application_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    submission_date = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    submission_deadline = models.DateField(
        null=True, blank=True, help_text="Document submission deadline")
    remarks = models.TextField(blank=True)
    # Admission details — filled by admin when marking as Verified
    semester = models.CharField(
        max_length=20, blank=True, help_text="e.g. 1st Semester")
    year_admitted = models.CharField(
        max_length=20, blank=True, help_text="e.g. 2025–2026")
    curriculum = models.CharField(
        max_length=100, blank=True, help_text="e.g. MIT 2023")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    program_level = models.CharField(
    max_length=50,
    blank=True,
    choices=[('masters', 'Master\'s Degree'), ('doctoral',
                                                'Doctoral Degree'), ('certificate', 'Certificate Program')],
    help_text="Program level (Masters, Doctoral, etc.)"
    )

    curriculum_data = models.JSONField(
    default=dict,
    blank=True,
    help_text="Structured curriculum data including courses, units, prerequisites, and level distribution"
    )

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

    document = models.OneToOneField(
        Document, on_delete=models.CASCADE, related_name='verification')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
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
        ('profile_updated', 'Updated Profile'),
        ('photo_updated', 'Changed Profile Photo'),
        ('cms_updated', 'Updated CMS Settings'),
    ]

    admin = models.ForeignKey(User, on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='admin_activities')
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name='activity_logs', null=True, blank=True)
    document = models.ForeignKey(
        Document, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Admin Activity Log'
        verbose_name_plural = 'Admin Activity Logs'

    def __str__(self):
        return f"{self.admin.username if self.admin else 'Unknown'} - {self.action} on {self.application.application_id if self.application else 'Profile'}"


class AdminProfile(models.Model):
    """
    Stores additional admin profile information including profile picture.
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='admin_profile')
    profile_picture = models.ImageField(
        upload_to='admin_profiles/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'

    def __str__(self):
        return f"Profile for {self.user.get_full_name() or self.user.username}"


class CMSSettings(models.Model):
    """
    Singleton model for controlling public-facing homepage content.
    Always use pk=1. Access via CMSSettings.objects.get_or_create(pk=1).
    """
    admissions_open = models.BooleanField(default=True)
    show_announcement = models.BooleanField(default=True)
    # JSON list of {text: str, duration: int (seconds)}
    announcements = models.JSONField(
        default=list,
        blank=True,
        help_text='List of announcements: [{text, duration}]'
    )
    hero_tagline = models.TextField(
        blank=True,
        default="Advance your professional journey. Our Master's programs are designed for the next generation of academic and industry leaders."
    )
    application_deadline = models.DateField(null=True, blank=True)
    # JSON list of {name: str, degree: str, description: str, visible: bool}
    programs = models.JSONField(
        default=list,
        blank=True,
        help_text='List of programs: [{name, degree, description, visible}]'
    )
    # JSON list of {name: str, url: str, file_type: str}
    downloads = models.JSONField(
        default=list,
        blank=True,
        help_text='List of downloadable files: [{name, url, file_type}]'
    )
    # Program Details (MIT Program CMS)
    program_name = models.CharField(
        max_length=255,
        blank=True,
        default="Master in Information Technology"
    )
    program_degree = models.CharField(
        max_length=255,
        blank=True,
        default="MIT"
    )
    program_title = models.CharField(
        max_length=255,
        blank=True,
        default="Master in Information Technology"
    )
    program_tagline = models.TextField(
        blank=True,
        default="Preparing professionals for the industrial practice of systems integration, administration, planning, implementation, and the maintenance of complex technology ecosystems."
    )
    program_description = models.TextField(
        blank=True,
        help_text="Main description of the program"
    )
    program_institution = models.CharField(
        max_length=255,
        blank=True,
        default="Western Mindanao State University, Zamboanga City"
    )
    program_copc_number = models.CharField(
        max_length=100,
        blank=True,
        default="017, Series of 2019 – issued August 28, 2019"
    )
    program_effective_year = models.CharField(
        max_length=50,
        blank=True,
        default="2019–2020"
    )
    program_accreditor = models.CharField(
        max_length=255,
        blank=True,
        default="Commission on Higher Education (CHED), Republic of the Philippines"
    )
    # JSON list of {title: str, description: str}
    program_objectives = models.JSONField(
        default=list,
        blank=True,
        help_text='List of program objectives: [{title, description}]'
    )
    # JSON list of {number: int, title: str, description: str}
    program_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text='List of learning outcomes: [{number, title, description}]'
    )
    # JSON list of {title: str, courses: [{code: str, name: str, units: int}]}
    program_curriculum = models.JSONField(
        default=list,
        blank=True,
        help_text='Program curriculum structure with course groups'
    )
    # JSON list of {stat_label: str, stat_value: str}
    program_stats = models.JSONField(
        default=list,
        blank=True,
        help_text='Program statistics: [{stat_label, stat_value}]'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'CMS Settings'

    def __str__(self):
        return 'Homepage CMS Settings'


class Faculty(models.Model):
    """
    Stores faculty member information for the program.
    """
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    title = models.CharField(
        max_length=255,
        help_text="e.g., Associate Professor, Instructor"
    )
    specializations = models.TextField(
        blank=True,
        help_text="Comma-separated list of specializations"
    )
    photo = models.ImageField(
        upload_to='faculty/', null=True, blank=True)
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order in the faculty list"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Faculty'
        verbose_name_plural = 'Faculty'
        ordering = ['order', 'last_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}".upper()


class RequirementType(models.Model):
    """
    Defines the types of requirements that students need to submit.
    Admin can create, edit, and manage requirement types.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="e.g., PSA Birth Certificate, Transcript of Records"
    )
    description = models.TextField(
        blank=True, help_text="Optional description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Requirement Type'
        verbose_name_plural = 'Requirement Types'
        ordering = ['name']

    def __str__(self):
        return self.name


class StudentRequirement(models.Model):
    """
    Tracks which requirements a student is missing.
    Admin can mark students as lacking specific requirements.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('notified', 'Notified'),
        ('submitted', 'Submitted'),
        ('waived', 'Waived'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='missing_requirements')
    requirement = models.ForeignKey(
        RequirementType, on_delete=models.CASCADE, related_name='student_requirements')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, help_text="Additional notes")
    notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Requirement'
        verbose_name_plural = 'Student Requirements'
        unique_together = ['user', 'requirement']
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.requirement.name}"


class RequirementNotification(models.Model):
    """
    Stores notification history sent to students about missing requirements.
    """
    student_requirement = models.ForeignKey(
        StudentRequirement, on_delete=models.CASCADE, related_name='notifications')
    sent_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Requirement Notification'
        verbose_name_plural = 'Requirement Notifications'
        ordering = ['-sent_at']

    def __str__(self):
        return f"Notification to {self.student_requirement.user.username} - {self.student_requirement.requirement.name}"
