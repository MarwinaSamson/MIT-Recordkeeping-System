import json

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import (
    Document,
    EducationalBackground,
    PersonalDetails,
    PrivacyConsent,
    WorkingStudent,
)

DOCUMENT_KEY_MAP = {
    "deans_recommendation": "deansRec",
    "tor": "tor",
    "honorable_dismissal": "honorableDismissal",
    "psa": "psa",
    "gsat": "gsat",
}


def _renderable_name(personal, user):
    if personal and personal.first_name and personal.last_name:
        return f"{personal.first_name} {personal.last_name}"
    if user.get_full_name():
        return user.get_full_name()
    return user.email or "Student"


def _initials(name):
    parts = [part for part in name.split() if part]
    if not parts:
        return "ST"
    return "".join([p[0] for p in parts])[:2].upper()


@login_required
def student(request):
    personal = PersonalDetails.objects.filter(user=request.user).first()
    education = EducationalBackground.objects.filter(user=request.user)
    working = WorkingStudent.objects.filter(user=request.user).first()
    documents = Document.objects.filter(user=request.user)
    privacy = PrivacyConsent.objects.filter(user=request.user).order_by("-updated_at").first()

    # Get application for status
    from admin_app.models import Application, DocumentVerification
    application = Application.objects.filter(user=request.user).first()

    # Calculate document verification counts
    verified_count = DocumentVerification.objects.filter(
        document__user=request.user, status='verified'
    ).count()
    reviewing_count = DocumentVerification.objects.filter(
        document__user=request.user, status='reviewing'
    ).count()

    document_files = {
        "deansRec": None,
        "tor": None,
        "honorableDismissal": None,
        "psa": None,
        "gsat": None,
    }
    document_urls = {
        "deansRec": None,
        "tor": None,
        "honorableDismissal": None,
        "psa": None,
        "gsat": None,
    }
    for document in documents:
        key = DOCUMENT_KEY_MAP.get(document.document_type)
        if key:
            document_files[key] = document.file_name or document.file.name
            document_urls[key] = document.file.url

    education_summary = {
        "college": "—",
        "graduate": "—",
    }
    for entry in education:
        if entry.level == "college":
            education_summary["college"] = entry.school_name or "—"
        if entry.level == "graduate":
            education_summary["graduate"] = entry.school_name or "—"

    full_name = _renderable_name(personal, request.user)
    initials = _initials(full_name)

    personal_json = {
        "firstName": personal.first_name if personal else "",
        "lastName": personal.last_name if personal else "",
        "dob": personal.dob.isoformat() if personal and personal.dob else "",
        "gender": personal.gender if personal else "",
        "contact": personal.contact_number if personal else "",
        "email": personal.email if personal else request.user.email,
        "address": personal.permanent_address if personal else "",
    }

    context = {
        "student": request.user,
        "personal_details": personal,
        "educational_background": education,
        "working_student": working,
        "privacy_consent": privacy,
        "document_files": document_files,
        "uploaded_documents": documents.count(),
        "required_documents": len(document_files),
        "verified_documents": verified_count,
        "reviewing_documents": reviewing_count,
        "full_name": full_name,
        "initials": initials,
        "undergrad_school": education_summary["college"],
        "graduate_school": education_summary["graduate"],
        "personal_json": json.dumps(personal_json),
        "document_files_json": json.dumps(document_files),
        "document_urls_json": json.dumps(document_urls),
        "application": application,
        "application_status": application.status if application else "pending",
        "submission_deadline": application.submission_deadline.strftime('%B %d, %Y') if application and application.submission_deadline else "TBA",
    }

    return render(request, "students_app/student.html", context)