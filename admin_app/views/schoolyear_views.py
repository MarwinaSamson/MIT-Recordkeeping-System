import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

from admin_app.models import SchoolYear, Semester


def is_admin(user):
    return user.is_authenticated and user.is_staff


# ──────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────

def serialize_school_year(sy):
    """Return a dict representation of a SchoolYear for JSON responses."""
    return {
        'id': sy.pk,
        'name': sy.name,
        'status': sy.status,
        'status_display': sy.get_status_display(),
        'start_date': sy.start_date.isoformat() if sy.start_date and hasattr(sy.start_date, 'isoformat') else sy.start_date,
        'end_date': sy.end_date.isoformat() if sy.end_date and hasattr(sy.end_date, 'isoformat') else sy.end_date,
        'date_range_display': sy.get_date_range_display(),
        'notes': sy.notes,
        'is_active': sy.is_active,
        'is_archived': sy.is_archived,
        'archived_at': sy.archived_at.isoformat() if sy.archived_at else None,
        'created_at': sy.created_at.isoformat(),
        'updated_at': sy.updated_at.isoformat(),
    }


def _semester_display_name(semester_number):
    labels = {
        1: '1st Semester',
        2: '2nd Semester',
        3: 'Summer',
    }
    return labels.get(int(semester_number), 'Semester')


def _normalize_semester_value(value):
    text = (value or '').strip().lower()
    if text in {'1', '1st', 'first', '1st semester', 'first semester'} or '1st' in text or 'first' in text:
        return '1st Semester'
    if text in {'2', '2nd', 'second', '2nd semester', 'second semester'} or '2nd' in text or 'second' in text:
        return '2nd Semester'
    if 'summer' in text:
        return 'Summer'
    return value or ''


def serialize_semester(semester):
    return {
        'id': semester.pk,
        'school_year_id': semester.school_year_id,
        'semester_number': semester.semester_number,
        'name': semester.name,
        'start_date': semester.start_date.isoformat() if semester.start_date else None,
        'end_date': semester.end_date.isoformat() if semester.end_date else None,
        'enrollment_limit': semester.enrollment_limit,
        'enrollment_count': semester.get_enrollment_count(),
        'notes': semester.notes,
        'is_active': semester.is_active,
        'is_configured': semester.is_configured,
        'created_at': semester.created_at.isoformat(),
        'updated_at': semester.updated_at.isoformat(),
    }


def _parse_iso_date(value):
    """Parse an ISO date string (YYYY-MM-DD) into a date object. Return None if empty/invalid."""
    if not value:
        return None
    if hasattr(value, 'strftime'):
        return value
    if isinstance(value, str):
        try:
            # datetime.fromisoformat handles 'YYYY-MM-DD' and full ISO timestamps
            return datetime.fromisoformat(value).date()
        except ValueError:
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except Exception:
                return None
    return None


def _parse_optional_int(value):
    if value in (None, ''):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


# ──────────────────────────────────────────────
# GET  /admin/school-years/summary/
# Returns counts for the dashboard summary cards
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def school_year_summary(request):
    active_count = SchoolYear.objects.filter(is_active=True).count()
    archived_count = SchoolYear.objects.filter(is_archived=True).count()
    upcoming_count = SchoolYear.objects.filter(
        is_archived=False,
        is_active=False,
        status__in=['draft', 'enrollment-open', 'enrollment-closed']
    ).count()

    active_sy = SchoolYear.objects.filter(is_active=True).first()

    return JsonResponse({
        'active_count': active_count,
        'archived_count': archived_count,
        'upcoming_count': upcoming_count,
        'active_school_year': serialize_school_year(active_sy) if active_sy else None,
    })


# ──────────────────────────────────────────────
# GET  /admin/school-years/
# Returns all non-archived school years grouped by status filter
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def list_school_years(request):
    status_filter = request.GET.get('status', '')  # 'active' | 'upcoming' | 'draft'

    qs = SchoolYear.objects.filter(is_archived=False)

    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'upcoming':
        qs = qs.filter(
            is_active=False,
            status__in=['enrollment-open', 'enrollment-closed']
        )
    elif status_filter == 'draft':
        qs = qs.filter(is_active=False, status='draft')

    data = [serialize_school_year(sy) for sy in qs]
    return JsonResponse({'school_years': data})


# ──────────────────────────────────────────────
# GET  /admin/school-years/<id>/semesters/
# Returns all semester records for a school year
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['GET'])
def list_school_year_semesters(request, school_year_id):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    sy.ensure_default_semesters()
    semesters = sy.semesters.all().order_by('semester_number')
    active_semester = sy.get_active_semester()

    return JsonResponse({
        'school_year': serialize_school_year(sy),
        'semesters': [serialize_semester(semester) for semester in semesters],
        'active_semester': serialize_semester(active_semester) if active_semester else None,
    })


# ──────────────────────────────────────────────
# GET  /admin/school-years/archived/
# Returns archived school years (with optional search/filter)
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def list_archived_school_years(request):
    search = request.GET.get('search', '').strip()
    year_filter = request.GET.get('year', '').strip()

    qs = SchoolYear.objects.filter(is_archived=True)

    if search:
        qs = qs.filter(name__icontains=search)
    if year_filter:
        qs = qs.filter(name=year_filter)

    data = [serialize_school_year(sy) for sy in qs]

    return JsonResponse({
        'archived_school_years': data,
        'total_archived': qs.count(),
        'last_updated': qs.order_by('-archived_at').values_list('archived_at', flat=True).first(),
    })


# ──────────────────────────────────────────────
# POST /admin/school-years/create/
# Creates a new school year
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def create_school_year(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    name = body.get('name', '').strip()
    status = body.get('status', 'draft')
    start_date = _parse_iso_date(body.get('start_date'))
    end_date = _parse_iso_date(body.get('end_date'))
    notes = body.get('notes', '').strip()
    is_active = body.get('is_active', False)

    if not name:
        return JsonResponse({'error': 'School year name is required.'}, status=400)

    # Validate format YYYY-YYYY
    parts = name.split('-')
    if len(parts) != 2 or not all(p.isdigit() and len(p) == 4 for p in parts):
        return JsonResponse({'error': 'Invalid format. Use YYYY-YYYY (e.g. 2028-2029).'}, status=400)

    if SchoolYear.objects.filter(name=name).exists():
        return JsonResponse({'error': f'School year "{name}" already exists.'}, status=400)

    # If setting as active, deactivate any currently active year
    if is_active:
        SchoolYear.objects.filter(is_active=True).update(is_active=False)

    sy = SchoolYear.objects.create(
        name=name,
        status=status,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
        is_active=is_active,
        created_by=request.user,
    )

    return JsonResponse({
        'success': True,
        'message': f'School year {name} created successfully.',
        'school_year': serialize_school_year(sy),
    }, status=201)


# ──────────────────────────────────────────────
# POST /admin/school-years/<id>/edit/
# Updates an existing school year
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def edit_school_year(request, school_year_id):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    name = body.get('name', sy.name).strip()
    status = body.get('status', sy.status)
    raw_start = body.get('start_date')
    raw_end = body.get('end_date')

    if raw_start is not None and raw_start != '':
        start_date = _parse_iso_date(raw_start)
    else:
        start_date = sy.start_date

    if raw_end is not None and raw_end != '':
        end_date = _parse_iso_date(raw_end)
    else:
        end_date = sy.end_date
    notes = body.get('notes', sy.notes).strip()

    # Validate name uniqueness (exclude self)
    if SchoolYear.objects.filter(name=name).exclude(pk=sy.pk).exists():
        return JsonResponse({'error': f'School year "{name}" already exists.'}, status=400)

    sy.name = name
    sy.status = status
    sy.start_date = start_date
    sy.end_date = end_date
    sy.notes = notes
    sy.save()

    return JsonResponse({
        'success': True,
        'message': f'School year {name} updated successfully.',
        'school_year': serialize_school_year(sy),
    })


# ──────────────────────────────────────────────
# POST /admin/school-years/<id>/activate/
# Sets a school year as the active one
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def activate_school_year(request, school_year_id):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    if sy.is_archived:
        return JsonResponse({'error': 'Cannot activate an archived school year.'}, status=400)

    sy.activate()

    return JsonResponse({
        'success': True,
        'message': f'{sy.name} is now the active school year.',
        'school_year': serialize_school_year(sy),
    })


# ──────────────────────────────────────────────
# POST /admin/school-years/<id>/archive/
# Archives a school year
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def archive_school_year(request, school_year_id):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    if sy.is_archived:
        return JsonResponse({'error': 'School year is already archived.'}, status=400)

    sy.archive()

    return JsonResponse({
        'success': True,
        'message': f'{sy.name} has been archived.',
        'school_year': serialize_school_year(sy),
    })


# ──────────────────────────────────────────────
# POST /admin/school-years/<id>/delete/
# Permanently deletes a school year (only drafts/archived)
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def delete_school_year(request, school_year_id):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    if sy.is_active:
        return JsonResponse({'error': 'Cannot delete the currently active school year.'}, status=400)

    name = sy.name
    sy.delete()

    return JsonResponse({
        'success': True,
        'message': f'School year {name} has been deleted.',
    })


# ──────────────────────────────────────────────
# POST /admin/school-years/<id>/semesters/<semester_number>/configure/
# Create or update semester dates and notes
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def configure_school_year_semester(request, school_year_id, semester_number):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    if sy.is_archived:
        return JsonResponse({'error': 'Cannot configure semesters for an archived school year.'}, status=400)

    if semester_number not in [1, 2, 3]:
        return JsonResponse({'error': 'Invalid semester selected.'}, status=400)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    start_date = _parse_iso_date(body.get('start_date'))
    end_date = _parse_iso_date(body.get('end_date'))
    enrollment_limit = _parse_optional_int(body.get('enrollment_limit'))
    notes = (body.get('notes') or '').strip()

    if not start_date or not end_date:
        return JsonResponse({'error': 'Start and end dates are required.'}, status=400)

    if start_date > end_date:
        return JsonResponse({'error': 'Start date cannot be later than end date.'}, status=400)

    semester, _ = Semester.objects.get_or_create(
        school_year=sy,
        semester_number=semester_number,
    )

    semester.start_date = start_date
    semester.end_date = end_date
    semester.enrollment_limit = enrollment_limit
    semester.notes = notes
    semester.save()

    return JsonResponse({
        'success': True,
        'message': f"{semester.name} configured successfully.",
        'semester': serialize_semester(semester),
    })


# ──────────────────────────────────────────────
# POST /admin/school-years/<id>/semesters/<semester_number>/activate/
# Sets a school year semester as active
# ──────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
@require_http_methods(['POST'])
def activate_school_year_semester(request, school_year_id, semester_number):
    try:
        sy = SchoolYear.objects.get(pk=school_year_id)
    except SchoolYear.DoesNotExist:
        return JsonResponse({'error': 'School year not found.'}, status=404)

    if sy.is_archived:
        return JsonResponse({'error': 'Cannot activate a semester for an archived school year.'}, status=400)

    if not sy.is_active:
        return JsonResponse({'error': 'Set the school year as active before activating a semester.'}, status=400)

    if semester_number not in [1, 2, 3]:
        return JsonResponse({'error': 'Invalid semester selected.'}, status=400)

    sy.ensure_default_semesters()
    try:
        semester = sy.semesters.get(semester_number=semester_number)
    except Semester.DoesNotExist:
        return JsonResponse({'error': 'Semester not found.'}, status=404)

    semester.activate()

    return JsonResponse({
        'success': True,
        'message': f'{semester.name} is now the active semester.',
        'semester': serialize_semester(semester),
        'semesters': [serialize_semester(item) for item in sy.semesters.all().order_by('semester_number')],
    })


# ──────────────────────────────────────────────
# GET  /api/student/school-year/
# Public endpoint: Returns the active school year for students
# Used by student dashboard to dynamically display current A.Y. and semester
# ──────────────────────────────────────────────

@login_required
@require_http_methods(['GET'])
def get_active_school_year(request):
    """
    Returns the currently active school year for the logged-in student.
    Also returns semester info if available.
    """
    active_sy = SchoolYear.objects.filter(is_active=True).first()

    if not active_sy:
        return JsonResponse({
            'active': False,
            'school_year': None,
            'semester': 'N/A',
            'message': 'No active school year set.',
        }, status=200)

    # Extract year range from name (e.g., "2025-2026" -> "2025", "2026")
    years = active_sy.name.split('-')
    year_start = years[0] if len(years) > 0 else ''
    year_end = years[1] if len(years) > 1 else ''

    # Determine current semester (1st or 2nd)
    # This is a simple heuristic: June-November = 1st Sem, December-May = 2nd Sem
    from datetime import datetime
    current_month = datetime.now().month
    fallback_semester = '1st Semester' if 6 <= current_month <= 11 else '2nd Semester'
    active_semester = active_sy.get_active_semester() if active_sy else None

    return JsonResponse({
        'active': True,
        'school_year': serialize_school_year(active_sy),
        'year_display': f'{year_start} – {year_end}',
        'year_start': year_start,
        'year_end': year_end,
        'semester': active_semester.name if active_semester else fallback_semester,
        'active_semester': serialize_semester(active_semester) if active_semester else None,
        'name': active_sy.name,
    }, status=200)