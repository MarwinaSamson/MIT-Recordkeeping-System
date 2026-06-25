"""
Utility functions for application status checks.
Used by login views, adapters, and middleware to determine user flow.
"""

import re

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


def normalize_curriculum_name(value):
    """Normalize legacy curriculum strings for matching."""
    text = (value or '').strip()
    if not text:
        return ''
    text = re.sub(r'^\s*(mit\s+)?curriculum\s*[:\-]?\s*', '', text, flags=re.I).strip()
    text = text.replace('–', '-').replace('—', '-')
    text = re.sub(r'\s+', ' ', text)
    return text


def resolve_canonical_curriculum_name(value):
    """Resolve a legacy curriculum string to a canonical Prospectus.name."""
    from admin_app.models import Prospectus

    raw = (value or '').strip()
    if not raw:
        return ''

    normalized = normalize_curriculum_name(raw)
    search_terms = [raw, normalized]
    if normalized:
        search_terms.extend([
            f'Curriculum {normalized}',
            f'MIT Curriculum {normalized}',
        ])

    for term in search_terms:
        if not term:
            continue
        prospectus = (
            Prospectus.objects.filter(name__iexact=term).first()
            or Prospectus.objects.filter(program__name__iexact=term).first()
            or Prospectus.objects.filter(description__iexact=term).first()
        )
        if prospectus:
            return prospectus.name

    for term in search_terms:
        if not term:
            continue
        prospectus = (
            Prospectus.objects.filter(name__icontains=term).first()
            or Prospectus.objects.filter(program__name__icontains=term).first()
        )
        if prospectus:
            return prospectus.name

    return ''
