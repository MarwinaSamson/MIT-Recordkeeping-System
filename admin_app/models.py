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
    # Navigation subtitle
    nav_subtitle = models.CharField(
        max_length=255,
        blank=True,
        default="MIT · Graduate School Admissions"
    )
    # Hero section fields
    hero_badge = models.CharField(
        max_length=100,
        blank=True,
        default="Graduate School · Information Technology"
    )
    hero_heading1 = models.CharField(
        max_length=255,
        blank=True,
        default="The University"
    )
    hero_heading2 = models.CharField(
        max_length=255,
        blank=True,
        default="of Choice"
    )
    hero_tagline = models.TextField(
        blank=True,
        default="Advance your professional journey with the Master of Information Technology program at WMSU Graduate School."
    )
    application_deadline = models.DateField(null=True, blank=True)
    app_window_ay = models.CharField(
        max_length=255,
        blank=True,
        default="Academic Year 2026–2027",
        help_text="Academic year label shown on the application window card"
    )
    app_window_enrollment = models.CharField(
        max_length=100,
        blank=True,
        default="July",
        help_text="Enrollment month label shown on the application window card"
    )
    app_window_deadline_year = models.CharField(
        max_length=10,
        blank=True,
        default="2026",
        help_text="Deadline year text shown on the application window card"
    )
    app_window_enrollment_year = models.CharField(
        max_length=10,
        blank=True,
        default="2026",
        help_text="Enrollment year text shown on the application window card"
    )
    app_stat_val1 = models.CharField(
        max_length=100,
        blank=True,
        default="MIT",
        help_text="First stat badge value shown in the application window card"
    )
    app_stat_label1 = models.CharField(
        max_length=100,
        blank=True,
        default="Program",
        help_text="Label for the first stat badge shown in the application window card"
    )
    app_stat_val2 = models.CharField(
        max_length=100,
        blank=True,
        default="4",
        help_text="Second stat badge value shown in the application window card"
    )
    app_stat_label2 = models.CharField(
        max_length=100,
        blank=True,
        default="Enrollment",
        help_text="Label for the second stat badge shown in the application window card"
    )
    cta_heading = models.CharField(
        max_length=255,
        blank=True,
        default="Ready to take the next step?",
        help_text="Call-to-action heading displayed in the application window card"
    )
    cta_sublabel = models.CharField(
        max_length=255,
        blank=True,
        default="Applications open for AY 2026–2027",
        help_text="Call-to-action sublabel displayed in the application window card"
    )
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
    # JSON list of event slides {title: str, date: str, day_label: str, time: str, venue: str, description: str, image_url: str, audience: str, featured: bool}
    event_slides = models.JSONField(
        default=list,
        blank=True,
        help_text='List of event slides for carousel: [{title, date, day_label, time, venue, description, image_url, audience, featured}]'
    )
    # JSON list of calendar events {id: int, month: int, day: int, title: str, type: str, tag: str, time: str, venue: str, audience: str, desc: str}
    calendar_events = models.JSONField(
        default=list,
        blank=True,
        help_text='List of calendar events: [{id, month, day, title, type, tag, time, venue, audience, desc}]'
    )
    # Contact information fields
    contact_address = models.CharField(
        max_length=255,
        blank=True,
        default="WMSU Main Campus, Normal Road, Baliwasan, Zamboanga City"
    )
    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        default="(062) 991-1771"
    )
    contact_email = models.EmailField(
        blank=True,
        default="admissions@wmsu.edu.ph"
    )
    contact_facebook = models.URLField(
        blank=True,
        help_text="Facebook page URL"
    )
    contact_hours = models.CharField(
        max_length=100,
        blank=True,
        default="Mon–Fri, 8AM–5PM"
    )
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
    # JSON list of admission requirements {number: int, title: str, description: str}
    admission_requirements = models.JSONField(
        default=list,
        blank=True,
        help_text='List of admission requirements: [{number, title, description}]'
    )
    # About page fields
    about_hero_eyebrow = models.CharField(
        max_length=255,
        blank=True,
        default="Western Mindanao State University · College of Computing Studies"
    )
    about_hero_title = models.CharField(
        max_length=255,
        blank=True,
        default="Master in"
    )
    about_hero_title_italic = models.CharField(
        max_length=255,
        blank=True,
        default="Information Technology"
    )
    about_hero_tagline = models.TextField(
        blank=True,
        default="Preparing professionals for systems integration, administration, planning, implementation, and maintenance of complex technology ecosystems."
    )
    about_hero_badge = models.CharField(
        max_length=255,
        blank=True,
        default="CHED Compliant · Effective S.Y. 2019–2020"
    )
    about_overview_text = models.TextField(
        blank=True,
        default="The Master in Information Technology (MIT) at Western Mindanao State University emphasizes the acquisition of advanced concepts and technologies, preparing graduates for the industrial practice of systems integration, systems administration, systems planning, and systems implementation — maintaining the integrity and proper functionality of complex systems."
    )
    about_overview_image = models.ImageField(
        upload_to='cms/about/',
        null=True,
        blank=True,
        help_text="Image shown in the right column of the About overview section"
    )
    # JSON list of {code: str, name: str, units: int, description: str}
    about_courses = models.JSONField(
        default=list,
        blank=True,
        help_text='List of courses: [{code, name, units, description}]'
    )
    # JSON list of {number: int, title: str, description: str}
    about_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text='List of learning outcomes: [{number, title, description}]'
    )
    # JSON list of {title: str, description: str}
    about_objectives = models.JSONField(
        default=list,
        blank=True,
        help_text='List of program objectives: [{title, description}]'
    )
    about_info_institution = models.TextField(
        blank=True,
        default="Western Mindanao State University"
    )
    about_info_copc = models.TextField(
        blank=True,
        default="017, Series of 2019 — August 28, 2019"
    )
    about_info_ay = models.CharField(
        max_length=100,
        blank=True,
        default="2019–2020"
    )
    about_info_accred = models.TextField(
        blank=True,
        default="Commission on Higher Education (CHED), Philippines"
    )
    about_ched_heading = models.CharField(
        max_length=255,
        blank=True,
        default="CHED Certified Program"
    )
    about_ched_desc = models.TextField(
        blank=True,
        default="Complies with CHED Resolution No. 405-2019 and Republic Act No. 7722 (Higher Education Act of 1994)."
    )
    about_stat1_val = models.CharField(
        max_length=100,
        blank=True,
        default="39"
    )
    about_stat1_lbl = models.CharField(
        max_length=100,
        blank=True,
        default="Total Units"
    )
    about_stat2_val = models.CharField(
        max_length=100,
        blank=True,
        default="2"
    )
    about_stat2_lbl = models.CharField(
        max_length=100,
        blank=True,
        default="Years Duration"
    )
    about_stat3_val = models.CharField(
        max_length=100,
        blank=True,
        default="12"
    )
    about_stat3_lbl = models.CharField(
        max_length=100,
        blank=True,
        default="Core Course Units"
    )
    about_stat4_val = models.CharField(
        max_length=100,
        blank=True,
        default="21"
    )
    about_stat4_lbl = models.CharField(
        max_length=100,
        blank=True,
        default="Specialization Units"
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
    
class SchoolYear(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('enrollment-open', 'Enrollment Open'),
        ('enrollment-closed', 'Enrollment Closed'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ]

    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2027-2028")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=False, help_text="Only one school year should be active at a time.")
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_school_years')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Year'
        verbose_name_plural = 'School Years'
        ordering = ['-name']

    def __str__(self):
        return self.name

    def get_date_range_display(self):
        if self.start_date and self.end_date:
            return f"{self.start_date.strftime('%b %d, %Y')} – {self.end_date.strftime('%b %d, %Y')}"
        return '—'

    def activate(self):
        SchoolYear.objects.filter(is_active=True).update(is_active=False)
        self.is_active = True
        self.status = 'active'
        self.save()

    def archive(self):
        from django.utils import timezone
        self.is_archived = True
        self.is_active = False
        self.status = 'archived'
        self.archived_at = timezone.now()
        self.save()


class Prospectus(models.Model):
    """
    Represents a prospectus/curriculum structure: Years -> Semesters -> Subjects
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    program_name = models.CharField(max_length=255, blank=True, help_text='Optional program name this prospectus applies to')
    program_code = models.CharField(max_length=64, blank=True, help_text='Optional program code')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_prospectuses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Program(models.Model):
    """Simple Program model to reference prospectuses."""
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProspectusYear(models.Model):
    prospectus = models.ForeignKey(Prospectus, related_name='years', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=120, default='Year')

    class Meta:
        ordering = ['order']
        unique_together = ('prospectus', 'order')

    def __str__(self):
        return f"{self.prospectus.name} – {self.label}"


class ProspectusSemester(models.Model):
    year = models.ForeignKey(ProspectusYear, related_name='semesters', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    label = models.CharField(max_length=120, default='Semester')

    class Meta:
        ordering = ['order']
        unique_together = ('year', 'order')

    def __str__(self):
        return f"{self.year} / {self.label}"


class ProspectusSubject(models.Model):
    semester = models.ForeignKey(ProspectusSemester, related_name='subjects', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    code = models.CharField(max_length=64, blank=True)
    title = models.CharField(max_length=512)
    prereq = models.CharField(max_length=255, blank=True)
    lec = models.PositiveSmallIntegerField(default=0)
    lab = models.PositiveSmallIntegerField(default=0)
    total = models.PositiveSmallIntegerField(default=0)
    grade = models.CharField(max_length=16, blank=True)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if not self.total:
            try:
                self.total = int(self.lec or 0) + int(self.lab or 0)
            except Exception:
                self.total = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} {self.title}"


class ProspectusAssignment(models.Model):
    prospectus = models.ForeignKey(Prospectus, related_name='assignments', on_delete=models.CASCADE)
    program_name = models.CharField(max_length=255, blank=True, help_text='Program name this prospectus is assigned to')
    program_code = models.CharField(max_length=64, blank=True, help_text='Optional program code')
    intake_year = models.CharField(max_length=32, blank=True, help_text='e.g., 2019-2020')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('program_name', 'intake_year')

    def __str__(self):
        target = self.program_name or self.intake_year or 'Unassigned'
        return f"{self.prospectus.name} → {target}"
