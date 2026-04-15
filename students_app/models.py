from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    Extended user profile to store email verification and session state.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    verification_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    token_created_at = models.DateTimeField(null=True, blank=True)
    is_email_verified = models.BooleanField(default=False)
    current_session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.email}"


class PersonalDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=120)
    middle_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120)
    dob = models.DateField()
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=64)
    civil_status = models.CharField(max_length=64)
    place_of_birth = models.CharField(max_length=255)
    religion = models.CharField(max_length=255)
    religion_other = models.CharField(max_length=255, blank=True)
    ethnicity = models.CharField(max_length=255)
    ethnicity_other = models.CharField(max_length=255, blank=True)
    nationality = models.CharField(max_length=255)
    nationality_other = models.CharField(max_length=255, blank=True)
    disability = models.CharField(max_length=255)
    disability_other = models.CharField(max_length=255, blank=True)
    permanent_address = models.CharField(max_length=500)
    current_address = models.CharField(max_length=500, blank=True)
    contact_number = models.CharField(max_length=50)
    email = models.EmailField()
    name_of_parent = models.CharField(max_length=255)
    relationship = models.CharField(max_length=128)
    parent_income = models.CharField(max_length=128)
    name_of_spouse = models.CharField(max_length=255, blank=True)
    spouse_contact_number = models.CharField(max_length=50, blank=True)
    spouse_income = models.CharField(max_length=128, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Personal details for {self.first_name} {self.last_name} ({self.email})"


class EducationalBackground(models.Model):
    LEVEL_CHOICES = [
        ('elementary', 'Elementary'),
        ('secondary', 'Secondary'),
        ('college', 'College'),
        ('graduate', 'Graduate Studies'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    school_name = models.CharField(max_length=255, blank=True)
    degree_course = models.CharField(max_length=255, blank=True)
    year_completed = models.PositiveIntegerField(null=True, blank=True)
    scholarship = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'level']

    def __str__(self):
        return f"{self.level.title()} background for {self.user.username if self.user else 'Unknown'}"


class WorkingStudent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_employed = models.BooleanField(default=False)
    position = models.CharField(max_length=255, blank=True)
    monthly_income = models.CharField(max_length=50, blank=True)
    employment_status = models.CharField(max_length=64, blank=True)
    employment_status_other = models.CharField(max_length=255, blank=True)
    employer_name = models.CharField(max_length=255, blank=True)
    employer_address = models.CharField(max_length=500, blank=True)
    employer_contact = models.CharField(max_length=50, blank=True)
    employer_classification = models.CharField(max_length=64, blank=True)
    employer_classification_other = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Working student data for {self.user.username if self.user else 'Unknown'}"


class PrivacyConsent(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    agreed = models.BooleanField(default=False)
    name = models.CharField(max_length=255, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.CharField(max_length=100, blank=True)
    form_version = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Privacy consent for {self.user.username if self.user else 'Unknown'}: {'agreed' if self.agreed else 'not agreed'}"


class Document(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('deans_recommendation', "Dean's Recommendation"),
        ('tor', 'Transcript of Records'),
        ('honorable_dismissal', 'Honorable Dismissal'),
        ('psa', 'PSA (Live Birth)'),
        ('gsat', 'GSAT (Graduate School Admission Test)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='documents/')
    file_name = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document_type} for {self.user.username if self.user else 'Unknown'}"

    def save(self, *args, **kwargs):
        if not self.file_name:
            self.file_name = self.file.name
        super().save(*args, **kwargs)


