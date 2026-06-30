import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction

from admin_app.models import DocumentVerification, Application, AdminNotification
from students_app.models import (
    Document,
    Notification,
    PersonalDetails,
    PrivacyConsent,
    CORSubmission,
    GradeSubmission,
    GradeEntry,
    StudentInboxMessage,
)


def _title_to_key(title):
    if not title:
        return ""
    return re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')


STATUS_MAP = {
    'verified':   'uploaded',
    'reviewing':  'review',
    'rejected':   'rejected',
    'incomplete': 'rejected',
    'pending':    'pending',
}


def _build_doc_lookup(user):
    lookup = {}
    for doc in Document.objects.filter(user=user):
        key = _title_to_key(doc.document_type)
        if key:
            lookup[key] = doc
    return lookup


def _build_verif_lookup(user):
    return {
        v.document_id: v
        for v in DocumentVerification.objects.filter(
            document__user=user
        ).select_related('document')
    }


def _get_cms_requirements():
    from admin_app.models import CMSSettings
    cms = CMSSettings.objects.get_or_create(pk=1)[0]
    return cms.admission_requirements or []


def _time_ago(dt):
    diff = (timezone.now() - dt).total_seconds()
    if diff < 60:     return 'Just now'
    if diff < 3600:   return f'{int(diff // 60)}m ago'
    if diff < 86400:  return f'{int(diff // 3600)}h ago'
    if diff < 172800: return 'Yesterday'
    return f'{int(diff // 86400)}d ago'


def _inbox_sender_meta(sent_by):
    """Display labels for inbox list / detail (admin vs system default)."""
    if not sent_by:
        return {
            'from': 'Office of the Registrar',
            'role': 'Registrar',
            'avatarInitials': 'OR',
            'avatarClass': 'registrar',
            'tag': 'registrar',
        }
    full = (sent_by.get_full_name() or '').strip()
    if not full:
        full = sent_by.email or sent_by.username
    parts = full.split()
    initials = ''.join(p[0] for p in parts[:2]).upper() if parts else 'AD'
    initials = initials[:2]
    return {
        'from': full,
        'role': 'Administration',
        'avatarInitials': initials,
        'avatarClass': 'admin',
        'tag': 'admin',
    }


@login_required
@require_http_methods(["GET"])
def get_document_status(request):
    requirements   = _get_cms_requirements()
    doc_by_key     = _build_doc_lookup(request.user)
    verif_by_docid = _build_verif_lookup(request.user)

    total_required = len(requirements)
    verified_count = reviewing_count = pending_count = missing_count = 0

    for req in requirements:
        key   = _title_to_key(req.get('title', ''))
        doc   = doc_by_key.get(key)

        if not doc:
            missing_count += 1
            continue

        verif = verif_by_docid.get(doc.id)
        if not verif:
            pending_count += 1
        elif verif.status == 'verified':
            verified_count += 1
        elif verif.status == 'reviewing':
            reviewing_count += 1
        elif verif.status in ('rejected', 'incomplete'):
            missing_count += 1
        else:
            pending_count += 1

    application = Application.objects.filter(user=request.user).first()
    deadline = (
        application.submission_deadline.strftime('%B %d, %Y')
        if application and application.submission_deadline else 'TBA'
    )

    return JsonResponse({
        'verified_documents':  verified_count,
        'reviewing_documents': reviewing_count,
        'pending_documents':   pending_count,
        'missing_documents':   missing_count,
        'total_documents':     total_required,
        'uploaded_documents':  total_required - missing_count,
        'application_status':  application.status if application else 'pending',
        'submission_deadline': deadline,
    })


@login_required
@require_http_methods(["GET"])
def get_document_details(request):
    requirements   = _get_cms_requirements()
    doc_by_key     = _build_doc_lookup(request.user)
    verif_by_docid = _build_verif_lookup(request.user)

    result = {}

    for req in requirements:
        title   = req.get('title', '')
        cms_key = _title_to_key(title)
        if not cms_key:
            continue

        doc = doc_by_key.get(cms_key)

        if not doc:
            result[cms_key] = {
                'status': 'missing', 'uploaded': False,
                'filename': None, 'rejection_reason': '', 'remarks': '',
            }
            continue

        verif = verif_by_docid.get(doc.id)

        if not verif:
            result[cms_key] = {
                'status': 'pending', 'uploaded': True,
                'filename': doc.file_name or doc.file.name,
                'rejection_reason': '', 'remarks': '',
            }
            continue

        result[cms_key] = {
            'status':           STATUS_MAP.get(verif.status, 'pending'),
            'uploaded':         True,
            'filename':         doc.file_name or doc.file.name,
            'rejection_reason': verif.rejection_reason or '',
            'remarks':          verif.remarks or '',
            'admin_status':     verif.status,
        }

    return JsonResponse(result)


@login_required
@require_http_methods(["POST"])
def upload_document(request):
    """Persist a single student document upload and reset any prior copy of the same requirement."""
    file_obj = request.FILES.get('file')
    doc_title = (request.POST.get('document_title') or '').strip()
    doc_key = (request.POST.get('document_key') or '').strip()

    if not file_obj:
        return JsonResponse({'success': False, 'message': 'No file was uploaded.'}, status=400)

    if not doc_title:
        if not doc_key:
            return JsonResponse({'success': False, 'message': 'Document title is required.'}, status=400)

        # Fallback: resolve the CMS requirement title from the slug key.
        resolved_title = ''
        for req in _get_cms_requirements():
            if _title_to_key(req.get('title', '')) == doc_key:
                resolved_title = req.get('title', '')
                break
        doc_title = resolved_title

    if not doc_title:
        return JsonResponse({'success': False, 'message': 'Unable to resolve the document title.'}, status=400)

    # Replace the previous copy of the same requirement so the admin side
    # sees the newest upload as pending review instead of still missing.
    Document.objects.filter(user=request.user, document_type=doc_title).delete()
    saved_doc = Document.objects.create(
        user=request.user,
        document_type=doc_title,
        file=file_obj,
    )

    full_name = request.user.get_full_name() or request.user.username
    AdminNotification.objects.create(
        notification_type='document_upload',
        student=request.user,
        title='Document Uploaded',
        message=f"{full_name} uploaded a {doc_title}.",
        related_object_id=saved_doc.pk,
    )

    return JsonResponse({
        'success': True,
        'message': 'Document uploaded successfully.',
        'document': {
            'id': saved_doc.id,
            'document_type': saved_doc.document_type,
            'file_name': saved_doc.file_name,
        },
    })


@login_required
@require_http_methods(["GET"])
def get_my_cor_submissions(request):
    subs = CORSubmission.objects.filter(user=request.user).order_by('-uploaded_at')
    data = []
    for s in subs:
        data.append({
            'id': s.id,
            'year_level': s.year_level,
            'semester': s.semester,
            'school_year': s.school_year,
            'status': s.status,
            'admin_remarks': s.admin_remarks or '',
            'file_url': s.cor_file.url if s.cor_file else '',
            'file_name': s.cor_file.name.split('/')[-1] if s.cor_file else '',
            'uploaded_at': s.uploaded_at.isoformat(),
        })
    return JsonResponse({'success': True, 'submissions': data})


@login_required
@require_http_methods(["POST"])
def upload_cor_submission(request):
    file_obj = request.FILES.get('file')
    year_level = (request.POST.get('year_level') or '').strip()
    semester = (request.POST.get('semester') or '').strip()
    school_year = (request.POST.get('school_year') or '').strip()

    if not file_obj:
        return JsonResponse({'success': False, 'message': 'No file uploaded.'}, status=400)
    if not semester or not school_year:
        return JsonResponse({'success': False, 'message': 'semester and school_year are required.'}, status=400)

    # Replace existing slot for this term so admin always sees latest
    CORSubmission.objects.filter(
        user=request.user,
        year_level=year_level,
        semester=semester,
        school_year=school_year,
    ).delete()

    sub = CORSubmission.objects.create(
        user=request.user,
        year_level=year_level,
        semester=semester,
        school_year=school_year,
        cor_file=file_obj,
        status='Pending',
    )

    return JsonResponse({
        'success': True,
        'message': 'COR uploaded.',
        'submission': {
            'id': sub.id,
            'year_level': sub.year_level,
            'semester': sub.semester,
            'school_year': sub.school_year,
            'status': sub.status,
            'admin_remarks': sub.admin_remarks or '',
            'file_url': sub.cor_file.url if sub.cor_file else '',
            'file_name': sub.cor_file.name.split('/')[-1] if sub.cor_file else '',
            'uploaded_at': sub.uploaded_at.isoformat(),
        }
    })


@login_required
@require_http_methods(["GET"])
def get_my_latest_grade_submission(request):
    sub = GradeSubmission.objects.filter(user=request.user).order_by('-uploaded_at').first()
    if not sub:
        return JsonResponse({'success': True, 'submission': None})
    entries = []
    for e in GradeEntry.objects.filter(submission=sub):
        entries.append({
            'code': e.code,
            'title': e.title,
            'units': e.units,
            'grade': float(e.grade) if e.grade is not None else None,
            'remarks': e.remarks or '',
        })
    return JsonResponse({
        'success': True,
        'submission': {
            'id': sub.id,
            'semester': sub.semester,
            'school_year': sub.school_year,
            'gpa': float(sub.gpa) if sub.gpa is not None else None,
            'status': sub.status,
            'admin_remarks': sub.admin_remarks or '',
            'screenshot_url': sub.screenshot.url if sub.screenshot else '',
            'uploaded_at': sub.uploaded_at.isoformat(),
            'entries': entries,
        },
    })


@login_required
@require_http_methods(["POST"])
def submit_grade_submission(request):
    """
    Multipart form:
      - semester, school_year, gpa (optional)
      - entries_json: JSON list of {code,title,units,grade}
      - screenshot (optional file)
    """
    latest = GradeSubmission.objects.filter(user=request.user).order_by('-uploaded_at').first()
    if latest and latest.status == 'Acknowledged':
        return JsonResponse({
            'success': False,
            'message': 'Your grades have already been acknowledged by the admin and can no longer be edited.',
        }, status=403)

    semester = (request.POST.get('semester') or '').strip()
    school_year = (request.POST.get('school_year') or '').strip()
    gpa_raw = (request.POST.get('gpa') or '').strip()
    entries_json = request.POST.get('entries_json') or '[]'
    screenshot = request.FILES.get('screenshot')

    if not semester or not school_year:
        return JsonResponse({'success': False, 'message': 'semester and school_year are required.'}, status=400)

    try:
        entries = json.loads(entries_json)
        if not isinstance(entries, list):
            entries = []
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid entries_json.'}, status=400)

    gpa_val = None
    if gpa_raw:
        try:
            gpa_val = float(gpa_raw)
        except ValueError:
            gpa_val = None

    # Create a new submission per save (history), admin verifies latest.
    # Carry over the previous screenshot if no new file was uploaded.
    inherited_screenshot = None
    if not screenshot and latest and latest.screenshot:
        inherited_screenshot = latest.screenshot

    sub = GradeSubmission.objects.create(
        user=request.user,
        semester=semester,
        school_year=school_year,
        gpa=gpa_val,
        screenshot=screenshot or inherited_screenshot,
        status='Pending',
    )

    cleaned_entries = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        code = str(item.get('code', '')).strip()
        title = str(item.get('title', '')).strip()
        try:
            units = int(item.get('units', 0) or 0)
        except (TypeError, ValueError):
            units = 0
        grade = item.get('grade', None)
        grade_val = None
        if grade is not None and grade != '':
            try:
                grade_val = float(grade)
            except (TypeError, ValueError):
                grade_val = None
        if not code:
            continue
        cleaned_entries.append(GradeEntry(
            submission=sub,
            code=code,
            title=title,
            units=max(0, units),
            grade=grade_val,
        ))

    if cleaned_entries:
        GradeEntry.objects.bulk_create(cleaned_entries)

    return JsonResponse({
        'success': True,
        'message': 'Grades submitted.',
        'submission_id': sub.id,
    })


ICON_MAP = {
    'document_verified':  ('fa-check-circle',  '#15803D', '#F0FDF4'),
    'document_rejected':  ('fa-times-circle',  '#DC2626', '#FEF2F2'),
    'document_reviewing': ('fa-search',        '#1D4ED8', '#EFF6FF'),
    'application_status': ('fa-file',          '#B45309', '#FFFBEB'),
    'deadline_reminder':  ('fa-bell',          '#B45309', '#FFFBEB'),
    'general':            ('fa-info-circle',   '#6B7280', '#F9FAFB'),
}


@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:20]

    data = []
    for n in notifications:
        icon, color, bg = ICON_MAP.get(n.notification_type, ICON_MAP['general'])
        data.append({
            'id': n.id, 'title': n.title, 'message': n.message,
            'type': n.notification_type, 'icon': icon,
            'color': color, 'bg': bg,
            'time': _time_ago(n.created_at), 'read': n.is_read,
        })

    return JsonResponse({
        'notifications': data,
        'unread_count': Notification.objects.filter(
            user=request.user, is_read=False
        ).count(),
    })


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request):
    try:
        data     = json.loads(request.body)
        notif_id = data.get('notification_id')
        Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
        return JsonResponse({
            'status': 'success',
            'unread_count': Notification.objects.filter(
                user=request.user, is_read=False
            ).count(),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success', 'unread_count': 0})


@login_required
@require_http_methods(["GET"])
def get_inbox_messages(request):
    """Inbox messages from administrators (separate from bell notifications)."""
    from django.utils.html import escape
    from django.utils.safestring import mark_safe

    qs = (
        StudentInboxMessage.objects.filter(user=request.user)
        .select_related('sent_by')
        .order_by('-created_at')[:100]
    )
    data = []
    for m in qs:
        meta = _inbox_sender_meta(m.sent_by)
        preview = (m.body or '').strip().replace('\n', ' ')
        if len(preview) > 160:
            preview = preview[:157] + '...'
        data.append({
            'id': m.id,
            'from': meta['from'],
            'role': meta['role'],
            'avatarClass': meta['avatarClass'],
            'avatarInitials': meta['avatarInitials'],
            'tag': meta['tag'],
            'subject': m.subject,
            'preview': preview,
            'body': mark_safe(escape(m.body or '').replace('\n', '<br>')),
            'time': _time_ago(m.created_at),
            'fullTime': m.created_at.strftime('%b %d, %Y · %I:%M %p'),
            'read': m.is_read,
        })

    return JsonResponse({
        'messages': data,
        'unread_count': StudentInboxMessage.objects.filter(
            user=request.user, is_read=False
        ).count(),
    })


@login_required
@require_http_methods(["POST"])
def mark_inbox_message_read(request):
    try:
        data = json.loads(request.body)
        mid = data.get('message_id')
        if mid is None:
            return JsonResponse({'status': 'error', 'message': 'message_id required'}, status=400)
        StudentInboxMessage.objects.filter(id=int(mid), user=request.user).update(is_read=True)
        return JsonResponse({
            'status': 'success',
            'unread_count': StudentInboxMessage.objects.filter(
                user=request.user, is_read=False
            ).count(),
        })
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid message_id'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def mark_all_inbox_messages_read(request):
    StudentInboxMessage.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success', 'unread_count': 0})


@login_required
@require_http_methods(["POST"])
def send_message_reply(request):
    """Student replies to an admin inbox message."""
    from students_app.models import StudentMessageReply
    try:
        data = json.loads(request.body)
        msg_id = data.get('message_id')
        body = (data.get('body') or '').strip()
        if not msg_id or not body:
            return JsonResponse({'status': 'error', 'message': 'message_id and body required'}, status=400)
        msg = StudentInboxMessage.objects.get(id=int(msg_id), user=request.user)
        reply = StudentMessageReply.objects.create(
            message=msg,
            sent_by=request.user,
            body=body,
        )
        return JsonResponse({
            'status': 'success',
            'reply_id': reply.id,
            'created_at': reply.created_at.strftime('%b %d, %Y %I:%M %p'),
        })
    except StudentInboxMessage.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Message not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def submit_application(request):
    try:
        data = json.loads(request.body)
        user = request.user

        pd_data = data.get('personalDetails', {})
        PersonalDetails.objects.update_or_create(
            user=user,
            defaults={
                'first_name':            pd_data.get('first_name', ''),
                'middle_name':           pd_data.get('middle_name', ''),
                'last_name':             pd_data.get('last_name', ''),
                'dob':                   pd_data.get('dob', ''),
                'age':                   pd_data.get('age') or None,
                'gender':                pd_data.get('gender', ''),
                'civil_status':          pd_data.get('civil_status', ''),
                'place_of_birth':        pd_data.get('place_of_birth', ''),
                'religion':              pd_data.get('religion', ''),
                'religion_other':        pd_data.get('religion_other', ''),
                'ethnicity':             pd_data.get('ethnicity', ''),
                'ethnicity_other':       pd_data.get('ethnicity_other', ''),
                'nationality':           pd_data.get('nationality', ''),
                'nationality_other':     pd_data.get('nationality_other', ''),
                'disability':            pd_data.get('disability', ''),
                'disability_other':      pd_data.get('disability_other', ''),
                'permanent_address':     pd_data.get('permanent_address', ''),
                'current_address':       pd_data.get('current_address', ''),
                'contact_number':        pd_data.get('contact_number', ''),
                'email':                 pd_data.get('email', ''),
                'name_of_parent':        pd_data.get('name_of_parent', ''),
                'relationship':          pd_data.get('relationship', ''),
                'parent_income':         pd_data.get('parent_income', ''),
                'name_of_spouse':        pd_data.get('name_of_spouse', ''),
                'spouse_contact_number': pd_data.get('spouse_contact_number', ''),
                'spouse_income':         pd_data.get('spouse_income', ''),
            }
        )

        mit_curriculum = data.get('mitCurriculum', '')
        if mit_curriculum:
            from students_app.models import EducationalBackground
            from students_app.utils import resolve_canonical_curriculum_name
            eb, _ = EducationalBackground.objects.get_or_create(
                user=user, level='college'
            )
            eb.mit_curriculum = resolve_canonical_curriculum_name(mit_curriculum) or mit_curriculum
            eb.save()

        privacy_data = data.get('privacyConsent', {})
        if privacy_data.get('agreed'):
            consent, _ = PrivacyConsent.objects.get_or_create(user=user)
            consent.agreed       = True
            consent.name         = privacy_data.get('name', '')
            consent.signed_at    = timezone.now()
            consent.user_agent   = privacy_data.get('userAgent', '')
            consent.ip_address   = request.META.get('REMOTE_ADDR', '')
            consent.form_version = privacy_data.get('formVersion', '1.0')
            consent.save()

        app_id   = f"MIT-{str(user.id).zfill(4)}"
        program  = data.get('educationalBackground', {}).get('program', '')
        existing = Application.objects.filter(user=user).first()

        if existing:
            existing.program        = program
            existing.status         = 'pending'
            existing.last_activity  = timezone.now()
            existing.application_id = app_id
            existing.save()
            application = existing
            is_new_application = False
        else:
            application = Application.objects.create(
                user=user, program=program,
                application_id=app_id, status='pending',
                last_activity=timezone.now(),
            )
            is_new_application = True

        # Notify admin of new enrollment application submission
        if is_new_application:
            try:
                from admin_app.models import AdminNotification
                full_name = user.get_full_name() or user.username
                AdminNotification.objects.create(
                    notification_type='enrollment_submitted',
                    student=user,
                    title='New Enrollment Application',
                    message=f"{full_name} submitted a new enrollment application ({application.application_id}).",
                    related_object_id=application.pk,
                )
            except Exception:
                pass

        return JsonResponse({
            'success': True,
            'message': 'Application submitted successfully',
            'application_id': application.application_id,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def update_profile(request):
    """Update the authenticated student's personal details."""
    try:
        data = json.loads(request.body)
        personal, _ = PersonalDetails.objects.get_or_create(user=request.user)

        if 'firstName' in data:
            personal.first_name = str(data['firstName']).strip()
        if 'lastName' in data:
            personal.last_name = str(data['lastName']).strip()
        if data.get('dob'):
            from datetime import date as date_cls
            try:
                personal.dob = date_cls.fromisoformat(str(data['dob']))
            except (ValueError, TypeError):
                pass
        if data.get('gender'):
            personal.gender = str(data['gender']).strip()
        if 'contact' in data:
            personal.contact_number = str(data['contact']).strip()
        if 'email' in data and data['email']:
            personal.email = str(data['email']).strip()
        if 'address' in data:
            personal.permanent_address = str(data['address']).strip()

        personal.save()

        first_name = personal.first_name or ''
        last_name = personal.last_name or ''
        if first_name or last_name:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save(update_fields=['first_name', 'last_name'])

        return JsonResponse({'success': True, 'message': 'Profile updated successfully.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@require_http_methods(["GET"])
def get_calendar_events(request):
    """Fetch current calendar events from CMS settings"""
    try:
        from admin_app.models import CMSSettings
        cms = CMSSettings.objects.get_or_create(pk=1)[0]
        calendar_events = cms.calendar_events or []
        return JsonResponse({
            'success': True,
            'events': calendar_events,
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'events': []
        }, status=500)