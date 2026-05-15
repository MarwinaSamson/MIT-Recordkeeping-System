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


def _normalize_curriculum_name(value):
    """Normalize curriculum names so legacy tokens can match canonical prospectus rows."""
    text = (value or "").strip()
    if not text:
        return ""
    text = re.sub(r'^\s*(mit\s+)?curriculum\s*[:\-]?\s*', '', text, flags=re.I).strip()
    text = text.replace('–', '-').replace('—', '-')
    text = re.sub(r'\s+', ' ', text)
    return text


def _resolve_student_prospectus(curriculum_name):
    """Resolve a student's curriculum token to a canonical Prospectus row."""
    from admin_app.models import Prospectus, ProspectusAssignment

    raw = (curriculum_name or '').strip()
    if not raw:
        return None

    normalized = _normalize_curriculum_name(raw)
    year_only = normalized

    search_terms = [raw, normalized]
    if normalized:
        search_terms.extend([
            f'Curriculum {normalized}',
            f'MIT Curriculum {normalized}',
        ])

    exact_filters = []
    for term in search_terms:
        if term:
            exact_filters.append({'name__iexact': term})
            exact_filters.append({'program_name__iexact': term})
            exact_filters.append({'description__iexact': term})

    # Try direct matches first.
    for filter_kwargs in exact_filters:
        prospectus = Prospectus.objects.filter(**filter_kwargs).prefetch_related('years__semesters__subjects').first()
        if prospectus:
            return prospectus

    # Check prospectus assignments using intake year mappings.
    if year_only:
        assignment = ProspectusAssignment.objects.select_related('prospectus').filter(intake_year__iexact=year_only).first()
        if assignment and assignment.prospectus:
            return assignment.prospectus

    # Fallback to substring matches so legacy records still resolve.
    for term in search_terms:
        if not term:
            continue
        prospectus = (
            Prospectus.objects.filter(name__icontains=term)
            .prefetch_related('years__semesters__subjects')
            .first()
            or Prospectus.objects.filter(program_name__icontains=term)
            .prefetch_related('years__semesters__subjects')
            .first()
        )
        if prospectus:
            return prospectus

    return None


@login_required
@ensure_csrf_cookie
def student(request):
    personal  = PersonalDetails.objects.filter(user=request.user).first()
    education = EducationalBackground.objects.filter(user=request.user)
    working   = WorkingStudent.objects.filter(user=request.user).first()
    documents = Document.objects.filter(user=request.user)
    privacy   = PrivacyConsent.objects.filter(
                    user=request.user).order_by("-updated_at").first()

    from admin_app.models import Application, DocumentVerification, SchoolYear, Semester, CMSSettings, Program, Prospectus

    application        = Application.objects.filter(user=request.user).first()
    active_school_year = SchoolYear.objects.filter(is_active=True).first()
    active_semester    = None
    if active_school_year:
        active_semester = Semester.objects.filter(
            school_year=active_school_year,
            is_active=True,
        ).first()
    if not active_semester:
        active_semester = Semester.objects.filter(is_active=True).select_related('school_year').first()
    cms_settings       = CMSSettings.objects.get_or_create(pk=1)[0]
    calendar_events        = cms_settings.calendar_events or []
    admission_requirements = cms_settings.admission_requirements or []
    downloads              = cms_settings.downloads or []

    semester = active_semester.name if active_semester else '—'

    program_display = Program.objects.order_by('name').values_list('name', flat=True).first() or '—'
    if application and application.program:
        program_key = application.program.strip()
        program_row = (
            Program.objects.filter(name__iexact=program_key).first()
            or Program.objects.filter(program_label__iexact=program_key).first()
            or Program.objects.filter(name__icontains=program_key).first()
            or Program.objects.filter(program_label__icontains=program_key).first()
        )
        if program_row:
            program_display = program_row.name

    student_id_display = application.application_id if application and application.application_id else '—'

    selected_curriculum_name = ''
    if application and application.curriculum:
        selected_curriculum_name = application.curriculum.strip()
    else:
        for entry in education:
            if entry.mit_curriculum:
                selected_curriculum_name = entry.mit_curriculum.strip()
                break

    prospectus_tree = []
    prospectus_title = selected_curriculum_name or '—'
    selected_prospectus = _resolve_student_prospectus(selected_curriculum_name)

    if selected_prospectus:
        prospectus_title = selected_prospectus.name
        selected_curriculum_name = selected_prospectus.name
        for year in selected_prospectus.years.all().order_by('order'):
            semesters_payload = []
            for semester_row in year.semesters.all().order_by('order'):
                courses_payload = []
                for subject in semester_row.subjects.all().order_by('order'):
                    courses_payload.append({
                        'code': subject.code,
                        'title': subject.title,
                        'lec': subject.lec,
                        'lab': subject.lab,
                        'prereq': subject.prereq,
                        'total': subject.total,
                        'grade': subject.grade,
                    })
                semesters_payload.append({
                    'id': semester_row.id,
                    'label': semester_row.label,
                    'courses': courses_payload,
                })
            prospectus_tree.append({
                'id': year.id,
                'label': year.label,
                'semesters': semesters_payload,
            })

    sy_display = active_school_year.name if active_school_year else '—'
    ay_display = active_school_year.name if active_school_year else '—'
    if active_school_year:
        sy_display = active_school_year.name
        ay_display = active_school_year.name

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
        "current_school_year_name":    active_school_year.name if active_school_year else "",
        "current_semester":            semester,
        "current_semester_name":       active_semester.name if active_semester else "",
        "program_display":            program_display,
        "student_id_display":         student_id_display,
        "selected_curriculum_name":    selected_curriculum_name,
        "prospectus_title":            prospectus_title,
        "prospectus_tree_json":        json.dumps(prospectus_tree),
        "calendar_events":             calendar_events,
        "calendar_events_json":        json.dumps(calendar_events),
        "admission_requirements":      admission_requirements,
        "admission_requirements_json": json.dumps(admission_requirements),
        "downloads":                   downloads,
    }

    return render(request, "students_app/student.html", context)
