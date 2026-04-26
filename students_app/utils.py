"""
Utility functions for application status checks.
Used by login views, adapters, and middleware to determine user flow.
"""

from students_app.models import (
    PersonalDetails,
    EducationalBackground,
    WorkingStudent,
    Document,
    PrivacyConsent,
)


def has_student_data(user):
    """
    Check if a user has any form data saved (partial application).
    Returns True if user has started filling out forms.
    """
    return (
        PersonalDetails.objects.filter(user=user).exists()
        or EducationalBackground.objects.filter(user=user).exists()
        or WorkingStudent.objects.filter(user=user).exists()
        or Document.objects.filter(user=user).exists()
    )


def has_completed_application(user):
    """
    Check if a user has officially submitted their application.
    Returns True only if user agreed to privacy notice and submitted.
    """
    privacy_consent = PrivacyConsent.objects.filter(user=user).first()
    return privacy_consent and privacy_consent.agreed


def get_user_redirect_url(user):
    """
    Determine the correct redirect URL for a user based on their role and application status.
    
    Logic:
    - If superuser → /admin-panel/dashboard/ (admin dashboard)
    - Else if application submitted (PrivacyConsent.agreed = True) → /student/ (dashboard)
    - Else if has any data (partial) → /personalDetails/ (continue forms)
    - Else → /personalDetails/ (start forms)
    """
    # Admin users always go to admin dashboard
    if user.is_superuser:
        return "/admin-panel/dashboard/"

    if has_completed_application(user):
        return "/student/"

    # Whether they have partial data or not, go to forms
    return "/personalDetails/"
