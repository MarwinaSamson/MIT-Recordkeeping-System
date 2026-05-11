from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..models import Document


def _get_cms():
    """Load CMS settings safely. Returns None if unavailable."""
    try:
        from admin_app.models import CMSSettings
        cms, _ = CMSSettings.objects.get_or_create(pk=1)
        return cms
    except Exception:
        return None


def _title_to_key(title: str) -> str:
    """
    Convert a requirement title to a safe HTML field-name key.
    e.g. "TOR (Transcript of Records)" → "tor_transcript_of_records"
    This is the SINGLE source of truth for key generation.
    The template must read req.field_key — never recompute via filters.
    """
    import re
    key = title.lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = key.strip("_")
    return key


def _save_document(user, doc_type: str, file_obj) -> None:
    """Save a single Document record."""
    if file_obj:
        Document(user=user, document_type=doc_type, file=file_obj).save()


def _enrich_requirements(raw_list: list) -> list:
    """
    Add a computed `field_key` to each requirement dict so the template
    never has to derive it independently (which caused the mismatch bug).
    Returns a new list — does not mutate the original CMS data.
    """
    enriched = []
    for req in raw_list:
        entry = dict(req)  # shallow copy so we don't dirty the cached model
        entry["field_key"] = _title_to_key(req.get("title", ""))
        enriched.append(entry)
    return enriched


@login_required
def documents(request):
    cms = _get_cms()

    from admin_app.models import Prospectus

    # Pull the CMS-driven requirements list and enrich with field_key.
    admission_requirements = []
    if cms and cms.admission_requirements:
        admission_requirements = _enrich_requirements(cms.admission_requirements)

    prospectuses = Prospectus.objects.filter(is_active=True).order_by('name')

    if request.method == "POST":
        validation_errors = []

        # ── Pass 1: validate all required fields before touching the DB ──
        for req in admission_requirements:
            title = req.get("title", "")
            required = req.get("required", False)
            multi_page = req.get("multi_page", False)
            field_key = req["field_key"]  # already computed — no recomputation

            if not required:
                continue  # optional — skip validation

            if multi_page:
                pdf_file = request.FILES.get(f"{field_key}_pdf")
                image_files = [
                    f for f in request.FILES.getlist(f"{field_key}_images[]")
                    if f
                ]
                if not (pdf_file or image_files):
                    validation_errors.append(
                        f'"{title}" is required. Please upload a PDF or at least one image.'
                    )
            else:
                file_obj = request.FILES.get(f"{field_key}_file")
                if not file_obj:
                    validation_errors.append(
                        f'"{title}" is required. Please upload the document.'
                    )

        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return render(request, "students_app/documents.html", {
                "admission_requirements": admission_requirements,
                "prospectuses": prospectuses,
            })

        # ── Pass 2: all required fields present — delete old docs & save ──
        Document.objects.filter(user=request.user).delete()

        for req in admission_requirements:
            title = req.get("title", "")
            multi_page = req.get("multi_page", False)
            field_key = req["field_key"]  # same key the template used for the input name

            if multi_page:
                pdf_file = request.FILES.get(f"{field_key}_pdf")
                image_files = [
                    f for f in request.FILES.getlist(f"{field_key}_images[]")
                    if f
                ]
                if pdf_file:
                    _save_document(request.user, title, pdf_file)
                else:
                    for img in image_files:
                        _save_document(request.user, title, img)
            else:
                file_obj = request.FILES.get(f"{field_key}_file")
                _save_document(request.user, title, file_obj)
        # Persist MIT Curriculum (form field `mitCurriculum`) to EducationalBackground
        mit_curriculum = request.POST.get("mitCurriculum", "").strip()
        if mit_curriculum:
            from students_app.models import EducationalBackground
            eb, _ = EducationalBackground.objects.get_or_create(user=request.user, level="college")
            eb.mit_curriculum = mit_curriculum
            eb.save()

        messages.success(
            request,
            "Documents saved successfully. You can add or modify documents later if needed."
        )
        return redirect("privacyNotice")

    # ── GET ───────────────────────────────────────────────────────────────
    return render(request, "students_app/documents.html", {
        "admission_requirements": admission_requirements,
        "prospectuses": prospectuses,
    })