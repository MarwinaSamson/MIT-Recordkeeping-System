import json
import re
from datetime import datetime

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from ..models import (
    Document,
    EducationalBackground,
    PersonalDetails,
    PrivacyConsent,
    WorkingStudent,
)


def _title_to_key(title):
    """
    Convert a document title to a slug key.
    Mirrors the frontend _titleToKey() exactly.
    e.g. 'Official Transcript of Records (TOR)' -> 'official_transcript_of_records_tor'
    """
    if not title:
        return ""
    key = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    return key


def _renderable_name(personal, user):
    if personal and personal.first_name and personal.last_name:
        return f"{personal.first_name} {personal.last_name}"
    if user.get_full_name():
        return user.get_full_name()
    return user.email or "Student"


def _initials(name):
    parts = [p for p in name.split() if p]
    if not parts:
        return "ST"
    return "".join([p[0] for p in parts])[:2].upper()


@login_required
@ensure_csrf_cookie
def student(request):
    personal  = PersonalDetails.objects.filter(user=request.user).first()
    education = EducationalBackground.objects.filter(user=request.user)
    working   = WorkingStudent.objects.filter(user=request.user).first()
    documents = Document.objects.filter(user=request.user)
    privacy   = PrivacyConsent.objects.filter(
                    user=request.user).order_by("-updated_at").first()

    from admin_app.models import Application, DocumentVerification, SchoolYear, CMSSettings

    application        = Application.objects.filter(user=request.user).first()
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    cms_settings       = CMSSettings.objects.get_or_create(pk=1)[0]
    calendar_events        = cms_settings.calendar_events or []
    admission_requirements = cms_settings.admission_requirements or []

    current_month = datetime.now().month
    semester = '1st Semester' if 6 <= current_month <= 11 else '2nd Semester'

    sy_display = "2025 – 2026"
    ay_display = "A.Y. 2025–2026"
    if active_school_year:
        years = active_school_year.name.split('-')
        sy_display = f"{years[0]} – {years[1]}" if len(years) == 2 else active_school_year.name
        ay_display = f"A.Y. {years[0]}–{years[1]}" if len(years) == 2 else f"A.Y. {active_school_year.name}"

    # ----------------------------------------------------------------
    # Build document lookup: slug_key -> Document
    # document_type in DB = exact CMS title, so slugs match directly
    # ----------------------------------------------------------------
    doc_by_key = {}
    for doc in documents:
        key = _title_to_key(doc.document_type)
        if key:
            doc_by_key[key] = doc

    # ----------------------------------------------------------------
    # Build verification lookup: slug_key -> DocumentVerification
    # ----------------------------------------------------------------
    verif_by_key = {}
    for dv in DocumentVerification.objects.filter(
            document__user=request.user).select_related('document'):
        key = _title_to_key(dv.document.document_type)
        if key:
            verif_by_key[key] = dv

    # ----------------------------------------------------------------
    # Build document_status_map keyed by CMS slugs
    # ----------------------------------------------------------------
    document_status_map = {}

    for req in admission_requirements:
        cms_key = _title_to_key(req.get('title', ''))
        if not cms_key:
            continue

        verif = verif_by_key.get(cms_key)
        doc   = doc_by_key.get(cms_key)

        if verif:
            vs = verif.status
            if vs == 'verified':
                display = 'uploaded'   # green "Verified"
            elif vs == 'reviewing':
                display = 'review'
            elif vs in ('rejected', 'incomplete'):
                display = 'missing'
            else:
                display = 'pending'
        elif doc:
            display = 'pending'
        else:
            display = 'missing'

        document_status_map[cms_key] = {
            'verification_status': display,
            'verification_id':     verif.id if verif else None,
            'cms_title':           req.get('title', ''),
        }

    # ----------------------------------------------------------------
    # document_files / document_urls keyed by CMS slug
    # ----------------------------------------------------------------
    document_files = {}
    document_urls  = {}
    for key, doc in doc_by_key.items():
        document_files[key] = doc.file_name or doc.file.name
        document_urls[key]  = doc.file.url

    # ----------------------------------------------------------------
    # Stats
    # ----------------------------------------------------------------
    submitted_count = sum(
        1 for v in document_status_map.values()
        if v['verification_status'] != 'missing'
    )
    verified_count = sum(
        1 for v in document_status_map.values()
        if v['verification_status'] == 'uploaded'
    )
    reviewing_count = sum(
        1 for v in document_status_map.values()
        if v['verification_status'] == 'review'
    )
    required_count = len(admission_requirements) if admission_requirements else len(doc_by_key)

    # ----------------------------------------------------------------
    # Education
    # ----------------------------------------------------------------
    education_summary = {"college": "—", "graduate": "—"}
    for entry in education:
        if entry.level == "college":
            education_summary["college"] = entry.school_name or "—"
        if entry.level == "graduate":
            education_summary["graduate"] = entry.school_name or "—"

    full_name = _renderable_name(personal, request.user)
    initials  = _initials(full_name)

    personal_json = {
        "firstName": personal.first_name        if personal else "",
        "lastName":  personal.last_name         if personal else "",
        "dob":       personal.dob.isoformat()   if personal and personal.dob else "",
        "gender":    personal.gender            if personal else "",
        "contact":   personal.contact_number    if personal else "",
        "email":     personal.email             if personal else request.user.email,
        "address":   personal.permanent_address if personal else "",
    }

    context = {
        "student":              request.user,
        "personal_details":     personal,
        "educational_background": education,
        "working_student":      working,
        "privacy_consent":      privacy,
        "document_files":       document_files,
        "uploaded_documents":   submitted_count,
        "required_documents":   required_count,
        "verified_documents":   verified_count,
        "reviewing_documents":  reviewing_count,
        "full_name":            full_name,
        "initials":             initials,
        "undergrad_school":     education_summary["college"],
        "graduate_school":      education_summary["graduate"],
        "personal_json":        json.dumps(personal_json),
        "document_files_json":  json.dumps(document_files),
        "document_urls_json":   json.dumps(document_urls),
        "document_status_map_json": json.dumps(document_status_map),
        "application":          application,
        "application_status":   application.status if application else "pending",
        "submission_deadline":  (
            application.submission_deadline.strftime('%B %d, %Y')
            if application and application.submission_deadline else "TBA"
        ),
        "active_school_year":          active_school_year,
        "school_year_display":         sy_display,
        "academic_year_display":       ay_display,
        "current_semester":            semester,
        "calendar_events":             calendar_events,
        "calendar_events_json":        json.dumps(calendar_events),
        "admission_requirements":      admission_requirements,
        "admission_requirements_json": json.dumps(admission_requirements),
    }

    return render(request, "students_app/student.html", context)