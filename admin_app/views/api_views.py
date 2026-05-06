"""
API views for admin dashboard actions.
Handles document verification, rejection, and application status updates.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.core.files.storage import default_storage
import json

from ..models import Application, DocumentVerification, AdminActivityLog, AdminProfile, SchoolYear
from students_app.models import Document
from ..models import Prospectus, ProspectusYear, ProspectusSemester, ProspectusSubject, ProspectusAssignment, Program

def is_superuser(user):
    """Check if user is a superuser."""
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admission_semesters(request):
    """Return distinct semester labels derived from ProspectusSemester labels."""
    try:
        labels = ProspectusSemester.objects.values_list('label', flat=True).distinct()
        return JsonResponse({'success': True, 'semesters': list(labels)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admission_school_years(request):
    """Return non-archived school years for admin dropdowns."""
    try:
        qs = SchoolYear.objects.filter(is_archived=False).order_by('-name')
        data = [{'id': sy.pk, 'name': sy.name, 'is_active': sy.is_active} for sy in qs]
        return JsonResponse({'success': True, 'school_years': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def get_admission_curricula(request):
    """Return active prospectuses as curricula options."""
    try:
        qs = Prospectus.objects.filter(is_active=True).order_by('-created_at')
        data = [{'id': p.pk, 'name': p.name, 'program_name': p.program_name, 'description': p.description} for p in qs]
        return JsonResponse({'success': True, 'curricula': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)



@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def verify_document(request):
    """Verify a document and update its status."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')

        # Get the application
        app = Application.objects.get(application_id=app_id)

        # Get the document
        doc = Document.objects.get(id=doc_id, user=app.user)

        # Get or create verification record
        verification, created = DocumentVerification.objects.get_or_create(
            document=doc)
        verification.status = 'verified'
        verification.verified_by = request.user
        verification.verified_at = timezone.now()
        verification.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='verified',
            application=app,
            document=doc,
            notes=f"Document verified."
        )

        return JsonResponse({
            'success': True,
            'message': f'Document {doc.file_name} marked as verified.',
            'status': 'verified'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reject_document(request):
    """Reject a document and record the reason."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')
        reason = data.get('reason', 'Document rejected.')

        # Get the application
        app = Application.objects.get(application_id=app_id)

        # Get the document
        doc = Document.objects.get(id=doc_id, user=app.user)

        # Get or create verification record
        verification, created = DocumentVerification.objects.get_or_create(
            document=doc)
        verification.status = 'rejected'
        verification.rejection_reason = reason
        verification.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='rejected',
            application=app,
            document=doc,
            notes=f"Document rejected: {reason}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Document {doc.file_name} marked as rejected.',
            'status': 'rejected'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reset_document_verification(request):
    """Reset document verification status back to pending/under review."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        doc_id = data.get('document_id')

        # Get the application
        app = Application.objects.get(application_id=app_id)

        # Get the document
        doc = Document.objects.get(id=doc_id, user=app.user)

        # Get verification record
        try:
            verification = DocumentVerification.objects.get(document=doc)
            old_status = verification.status
            verification.status = 'reviewing'
            verification.verified_by = None
            verification.verified_at = None
            verification.rejection_reason = ''
            verification.save()

            # Log the activity
            AdminActivityLog.objects.create(
                admin=request.user,
                action='resubmit',
                application=app,
                document=doc,
                notes=f"Document verification reset from {old_status} to reviewing."
            )

            return JsonResponse({
                'success': True,
                'message': f'Document {doc.file_name} verification reset.',
                'status': 'reviewing'
            })
        except DocumentVerification.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No verification record found for this document.'
            }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_application_status(request):
    """Update application status (verified, incomplete, etc.)."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        status = data.get('status')
        remarks = data.get('remarks', '')

        # Get the application
        app = Application.objects.get(application_id=app_id)
        app.status = status
        app.remarks = remarks
        app.last_activity = timezone.now()

        # Save admission details if provided (on verify)
        if 'semester' in data:
            app.semester = data.get('semester', '').strip()
        if 'year_admitted' in data:
            app.year_admitted = data.get('year_admitted', '').strip()
        if 'program_level' in data:
            app.program_level = data.get('program_level', '').strip()
        if 'curriculum_data' in data:
            app.curriculum_data = data.get('curriculum_data', {})

        app.save()

        # Log the activity
        action_map = {
            'verified': 'verified',
            'incomplete': 'incomplete',
            'rejected': 'rejected'
        }
        AdminActivityLog.objects.create(
            admin=request.user,
            action=action_map.get(status, 'note'),
            application=app,
            notes=f"Application status changed to {status}. {remarks}"
        )

        return JsonResponse({
            'success': True,
            'message': f'Application status updated to {status}.',
            'status': status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_remarks(request):
    """Update application remarks."""
    try:
        data = json.loads(request.body)
        app_id = data.get('application_id')
        remarks = data.get('remarks', '')

        # Get the application
        app = Application.objects.get(application_id=app_id)
        app.remarks = remarks
        app.last_activity = timezone.now()
        app.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=app,
            notes=f"Remarks updated: {remarks}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Remarks updated successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_admin_profile(request):
    """Update admin profile information (first name, last name, email)."""
    try:
        data = json.loads(request.body)
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()

        # Validate inputs
        if not first_name or not last_name or not email:
            return JsonResponse({
                'success': False,
                'message': 'All fields are required.'
            }, status=400)

        # Check if email is already used by another user
        from django.contrib.auth.models import User
        if User.objects.filter(email=email).exclude(id=request.user.id).exists():
            return JsonResponse({
                'success': False,
                'message': 'This email is already in use.'
            }, status=400)

        # Update user profile
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='profile_updated',
            notes=f"Updated profile: {first_name} {last_name} ({email})"
        )

        return JsonResponse({
            'success': True,
            'message': 'Profile updated successfully.',
            'data': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'full_name': user.get_full_name()
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def upload_admin_photo(request):
    """Upload admin profile photo."""
    try:
        if 'photo' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No photo file provided.'
            }, status=400)

        photo_file = request.FILES['photo']

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if photo_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'message': 'Only JPG, PNG, and WEBP images are allowed.'
            }, status=400)

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if photo_file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'File size must not exceed 5MB.'
            }, status=400)

        # Get or create admin profile
        admin_profile, created = AdminProfile.objects.get_or_create(
            user=request.user)

        # Delete old photo if exists
        if admin_profile.profile_picture:
            if default_storage.exists(admin_profile.profile_picture.name):
                default_storage.delete(admin_profile.profile_picture.name)

        # Save new photo
        admin_profile.profile_picture = photo_file
        admin_profile.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='photo_updated',
            notes=f"Changed profile photo - {photo_file.name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Profile photo updated successfully.',
            'data': {
                'photo_url': admin_profile.profile_picture.url
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_cms_settings(request):
    """Update public homepage CMS settings."""
    try:
        data = json.loads(request.body)

        from ..models import CMSSettings

        # Get existing cms settings or use defaults
        try:
            cms = CMSSettings.objects.get(pk=1)
        except CMSSettings.DoesNotExist:
            CMSSettings.objects.create(pk=1)
            cms = CMSSettings.objects.get(pk=1)

        update_data = {
            'admissions_open': bool(data.get('admissions_open', cms.admissions_open)),
            'show_announcement': bool(data.get('show_announcement', cms.show_announcement)),
            'nav_subtitle': data.get('nav_subtitle', cms.nav_subtitle).strip(),
            'hero_badge': data.get('hero_badge', cms.hero_badge).strip(),
            'hero_heading1': data.get('hero_heading1', cms.hero_heading1).strip(),
            'hero_heading2': data.get('hero_heading2', cms.hero_heading2).strip(),
            'hero_tagline': data.get('hero_tagline', cms.hero_tagline).strip(),
            'app_window_ay': str(data.get('app_window_ay') or cms.app_window_ay or '').strip(),
            'app_window_enrollment': str(data.get('app_window_enrollment') or cms.app_window_enrollment or '').strip(),
            'app_window_deadline_year': str(data.get('app_window_deadline_year') or cms.app_window_deadline_year or '').strip(),
            'app_window_enrollment_year': str(data.get('app_window_enrollment_year') or cms.app_window_enrollment_year or '').strip(),
            'app_stat_val1': str(data.get('app_stat_val1') or cms.app_stat_val1 or '').strip(),
            'app_stat_label1': str(data.get('app_stat_label1') or cms.app_stat_label1 or '').strip(),
            'app_stat_val2': str(data.get('app_stat_val2') or cms.app_stat_val2 or '').strip(),
            'app_stat_label2': str(data.get('app_stat_label2') or cms.app_stat_label2 or '').strip(),
            'cta_heading': str(data.get('cta_heading') or cms.cta_heading or '').strip(),
            'cta_sublabel': str(data.get('cta_sublabel') or cms.cta_sublabel or '').strip(),
            'application_deadline': data.get('application_deadline') or None,
            'contact_address': data.get('contact_address', cms.contact_address).strip(),
            'contact_phone': data.get('contact_phone', cms.contact_phone).strip(),
            'contact_email': data.get('contact_email', cms.contact_email).strip(),
            'contact_facebook': data.get('contact_facebook', cms.contact_facebook).strip(),
            'contact_hours': data.get('contact_hours', cms.contact_hours).strip(),
        }

        # Validate and save announcements list [{text, duration}]
        raw_announcements = data.get('announcements', None)
        if raw_announcements is not None:
            cleaned = []
            for item in raw_announcements:
                text = str(item.get('text', '')).strip()
                try:
                    duration = max(3, int(item.get('duration', 5)))
                except (ValueError, TypeError):
                    duration = 5
                if text:
                    cleaned.append({'text': text, 'duration': duration})
            update_data['announcements'] = cleaned

        # Validate and save programs list [{name, degree, description, visible}]
        raw_programs = data.get('programs', None)
        if raw_programs is not None:
            cleaned_programs = []
            for p in raw_programs:
                name = str(p.get('name', '')).strip()
                degree = str(p.get('degree', '')).strip()
                description = str(p.get('description', '')).strip()
                visible = bool(p.get('visible', True))
                if name:
                    cleaned_programs.append({
                        'name': name,
                        'degree': degree,
                        'description': description,
                        'visible': visible,
                    })
            update_data['programs'] = cleaned_programs

        # Validate and save downloads list [{name, url, file_type}]
        raw_downloads = data.get('downloads', None)
        if raw_downloads is not None:
            cleaned_downloads = []
            for d in raw_downloads:
                name = str(d.get('name', '')).strip()
                url = str(d.get('url', '')).strip()
                file_type = str(d.get('file_type', '')).strip()
                if name and url:
                    cleaned_downloads.append({
                        'name': name,
                        'url': url,
                        'file_type': file_type,
                    })
            update_data['downloads'] = cleaned_downloads

        # Validate and save event slides list
        raw_event_slides = data.get('event_slides', None)
        if raw_event_slides is not None:
            cleaned_slides = []
            for slide in raw_event_slides:
                title = str(slide.get('title', '')).strip()
                if title:  # Only add if title exists
                    cleaned_slides.append({
                        'title': title,
                        'date': str(slide.get('date', '')).strip(),
                        'day_label': str(slide.get('day_label', '')).strip(),
                        'time': str(slide.get('time', '')).strip(),
                        'venue': str(slide.get('venue', '')).strip(),
                        'description': str(slide.get('description', '')).strip(),
                        'image_url': str(slide.get('image_url', '')).strip(),
                        'audience': str(slide.get('audience', '')).strip(),
                        'featured': bool(slide.get('featured', False)),
                    })
            update_data['event_slides'] = cleaned_slides

        saved_calendar_event = None
        raw_calendar_events = data.get('calendar_events', None)
        if raw_calendar_events is not None:
            cleaned_events = []
            for evt in raw_calendar_events:
                title = str(evt.get('title', '')).strip()
                if title:  # Only add if title exists
                    cleaned_events.append({
                        'id': int(evt.get('id', 0)),
                        'month': int(evt.get('month', 1)),
                        'day': int(evt.get('day', 1)),
                        'title': title,
                        'type': str(evt.get('type', 'cr')).strip(),
                        'tag': str(evt.get('tag', '')).strip(),
                        'time': str(evt.get('time', '')).strip(),
                        'venue': str(evt.get('venue', '')).strip(),
                        'audience': str(evt.get('audience', '')).strip(),
                        'desc': str(evt.get('desc', '')).strip(),
                    })
            update_data['calendar_events'] = cleaned_events

        raw_calendar_event = data.get('calendar_event', None)
        if raw_calendar_event is not None:
            existing_events = cms.calendar_events or []
            title = str(raw_calendar_event.get('title', '')).strip()
            if title:
                evt_id = int(raw_calendar_event.get('id') or 0)
                if evt_id <= 0:
                    existing_ids = [int(e.get('id', 0)) for e in existing_events if e.get('id') is not None]
                    evt_id = max(existing_ids, default=0) + 1

                event = {
                    'id': evt_id,
                    'month': int(raw_calendar_event.get('month', 1)),
                    'day': int(raw_calendar_event.get('day', 1)),
                    'title': title,
                    'type': str(raw_calendar_event.get('type', 'cr')).strip(),
                    'tag': str(raw_calendar_event.get('tag', '')).strip(),
                    'time': str(raw_calendar_event.get('time', '')).strip(),
                    'venue': str(raw_calendar_event.get('venue', '')).strip(),
                    'audience': str(raw_calendar_event.get('audience', '')).strip(),
                    'desc': str(raw_calendar_event.get('desc', '')).strip(),
                }
                saved_calendar_event = event
                updated = False
                for idx, evt in enumerate(existing_events):
                    if int(evt.get('id', 0)) == evt_id:
                        existing_events[idx] = event
                        updated = True
                        break
                if not updated:
                    existing_events.append(event)
                update_data['calendar_events'] = existing_events

        raw_calendar_event_delete = data.get('calendar_event_delete', None)
        if raw_calendar_event_delete is not None:
            existing_events = cms.calendar_events or []
            delete_id = int(raw_calendar_event_delete.get('id') or 0)
            if delete_id > 0:
                update_data['calendar_events'] = [
                    evt for evt in existing_events if int(evt.get('id', 0)) != delete_id
                ]

        # Validate and save admission requirements list
        raw_admission_requirements = data.get('admission_requirements', None)
        if raw_admission_requirements is not None:
            cleaned_requirements = []
            for req in raw_admission_requirements:
                title = str(req.get('title', '')).strip()
                if title:  # Only add if title exists
                    cleaned_requirements.append({
                        'number': int(req.get('number', 1)),
                        'title': title,
                        'description': str(req.get('description', '')).strip(),
                        'required': bool(req.get('required', False)),    # ← ADD THIS
                        'multi_page': bool(req.get('multi_page', False)), # ← ADD THIS
                    })
            update_data['admission_requirements'] = cleaned_requirements

        # Use bulk update for better performance
        CMSSettings.objects.filter(pk=1).update(**update_data)

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Homepage CMS settings updated.'
        )

        message = 'CMS settings saved.'
        if raw_calendar_event is not None:
            message = 'Calendar event saved.'
        elif raw_calendar_event_delete is not None:
            message = 'Calendar event deleted.'

        response_payload = {'success': True, 'message': message}
        if saved_calendar_event is not None:
            response_payload['saved_calendar_event'] = saved_calendar_event
        return JsonResponse(response_payload)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def bulk_upload_cms_settings(request):
    """Bulk upload CMS content from admin CSV import."""
    try:
        data = json.loads(request.body)
        section = str(data.get('section', '')).strip()
        mode = str(data.get('mode', 'replace')).strip().lower()
        rows = data.get('rows', []) or []

        from ..models import CMSSettings

        cms, _ = CMSSettings.objects.get_or_create(pk=1)

        if section == 'announcements':
            cleaned = []
            for item in rows:
                text = str(item.get('text', '')).strip()
                if not text:
                    continue
                try:
                    duration = int(item.get('duration_sec', item.get('duration', 5)) or 5)
                except (ValueError, TypeError):
                    duration = 5
                cleaned.append({'text': text, 'duration': max(3, duration)})

            if mode == 'append':
                cms.announcements = (cms.announcements or []) + cleaned
            else:
                cms.announcements = cleaned

        elif section == 'events':
            existing = cms.calendar_events or []
            max_id = max([int(evt.get('id', 0)) for evt in existing] + [0])
            cleaned = []
            for item in rows:
                title = str(item.get('title', '')).strip()
                if not title:
                    continue
                month = int(item.get('month', 1) or 1)
                day = int(item.get('day', 1) or 1)
                evt_id = item.get('id')
                if evt_id is None or str(evt_id).strip() == '':
                    max_id += 1
                    evt_id = max_id
                cleaned.append({
                    'id': int(evt_id),
                    'month': max(1, min(12, month)),
                    'day': max(1, min(31, day)),
                    'title': title,
                    'type': str(item.get('type', 'cr')).strip(),
                    'tag': str(item.get('tag', '')).strip(),
                    'time': str(item.get('time', '')).strip(),
                    'venue': str(item.get('venue', '')).strip(),
                    'audience': str(item.get('audience', '')).strip(),
                    'desc': str(item.get('description', item.get('desc', ''))).strip(),
                })
            cms.calendar_events = (existing + cleaned) if mode == 'append' else cleaned

        elif section == 'requirements':
            existing = cms.admission_requirements or []
            next_num = max([int(req.get('number', 0)) for req in existing] + [0]) + 1
            cleaned = []
            for item in rows:
                title = str(item.get('requirement_name', item.get('title', ''))).strip()
                if not title:
                    continue
                description = str(item.get('hint_text', item.get('description', ''))).strip()
                cleaned.append({
                    'number': next_num,
                    'title': title,
                    'description': description,
                    'required': bool(item.get('required', False)),    # ← ADD THIS
                    'multi_page': bool(item.get('multi_page', False)), # ← ADD THIS
                })
                next_num += 1
            cms.admission_requirements = (existing + cleaned) if mode == 'append' else cleaned

        elif section == 'outcomes':
            existing = cms.program_outcomes or []
            next_num = max([int(out.get('number', 0)) for out in existing] + [0]) + 1
            cleaned = []
            for item in rows:
                title = str(item.get('outcome_title', item.get('title', ''))).strip()
                if not title:
                    continue
                description = str(item.get('outcome_description', item.get('description', ''))).strip()
                cleaned.append({
                    'number': next_num,
                    'title': title,
                    'description': description,
                })
                next_num += 1
            cms.program_outcomes = (existing + cleaned) if mode == 'append' else cleaned

        elif section == 'objectives':
            existing = cms.program_objectives or []
            cleaned = []
            for item in rows:
                text = str(item.get('objective_text', '')).strip()
                if not text:
                    continue
                cleaned.append({'title': text, 'description': ''})
            cms.program_objectives = (existing + cleaned) if mode == 'append' else cleaned

        else:
            return JsonResponse({
                'success': False,
                'message': 'Unsupported bulk upload section.'
            }, status=400)

        cms.save()
        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_bulk_upload',
            notes=f'Bulk uploaded CMS section: {section}'
        )
        return JsonResponse({'success': True, 'message': 'Bulk upload saved.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def upload_cms_file(request):
    """Upload a file for CMS downloads section."""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'message': 'No file provided.'
            }, status=400)

        file = request.FILES['file']

        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'message': 'File size must not exceed 50MB.'
            }, status=400)

        # Save file to media/downloads
        from django.core.files.storage import default_storage
        file_path = f'downloads/{file.name}'
        path = default_storage.save(file_path, file)
        file_url = default_storage.url(path)

        # Get file extension for type
        import os
        _, ext = os.path.splitext(file.name)
        file_type = ext.lstrip('.').upper() if ext else 'FILE'

        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully.',
            'data': {
                'name': file.name,
                'url': file_url,
                'file_type': file_type
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error uploading file: {str(e)}'
        }, status=400)


# ============== Student Requirement Notification APIs ==============

@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_requirement_types(request):
    """Get all active requirement types."""
    from ..models import RequirementType

    types = RequirementType.objects.filter(is_active=True).order_by('name')
    data = [{'id': t.id, 'name': t.name, 'description': t.description}
            for t in types]
    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def create_requirement_type(request):
    """Create a new requirement type."""
    from ..models import RequirementType

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return JsonResponse({'success': False, 'message': 'Requirement name is required.'}, status=400)

        # Check if already exists
        if RequirementType.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'message': 'A requirement type with this name already exists.'}, status=400)

        req_type = RequirementType.objects.create(
            name=name, description=description)

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            notes=f"Created requirement type: {name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Requirement type created successfully.',
            'data': {'id': req_type.id, 'name': req_type.name, 'description': req_type.description}
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_requirement_type(request):
    """Delete a requirement type."""
    from ..models import RequirementType

    try:
        data = json.loads(request.body)
        type_id = data.get('requirement_type_id')

        if not type_id:
            return JsonResponse({'success': False, 'message': 'Requirement type ID is required.'}, status=400)

        req_type = RequirementType.objects.get(id=type_id)
        name = req_type.name
        req_type.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            notes=f"Deleted requirement type: {name}"
        )

        return JsonResponse({'success': True, 'message': 'Requirement type deleted successfully.'})
    except RequirementType.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Requirement type not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_students_with_requirements(request):
    """Get list of students with missing requirements."""
    from ..models import StudentRequirement, RequirementType
    from django.contrib.auth.models import User

    # Get filter parameters
    status = request.GET.get('status', '')
    requirement_id = request.GET.get('requirement_id', '')

    requirements = StudentRequirement.objects.select_related(
        'user', 'requirement')

    if status:
        requirements = requirements.filter(status=status)
    if requirement_id:
        requirements = requirements.filter(requirement_id=requirement_id)

    # Group by student
    student_data = {}
    for req in requirements:
        user_id = req.user.id
        if user_id not in student_data:
            user = req.user
            # Get application info
            app = Application.objects.filter(user=user).first()
            student_data[user_id] = {
                'user_id': user_id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name() or user.email,
                'application_id': app.application_id if app else None,
                'requirements': []
            }

        student_data[user_id]['requirements'].append({
            'id': req.id,
            'requirement_id': req.requirement.id,
            'requirement_name': req.requirement.name,
            'status': req.status,
            'notes': req.notes,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
            'updated_at': req.updated_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({'success': True, 'data': list(student_data.values())})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def list_prospectuses(request):
    """Return all prospectuses with nested years/semesters/subjects."""
    try:
        qs = Prospectus.objects.all().order_by('-created_at')
        out = []
        for p in qs:
            years = []
            for y in p.years.all().order_by('order'):
                sems = []
                for s in y.semesters.all().order_by('order'):
                    subs = []
                    for sub in s.subjects.all().order_by('order'):
                        subs.append({
                            'id': sub.id,
                            'order': sub.order,
                            'code': sub.code,
                            'title': sub.title,
                            'prereq': sub.prereq,
                            'lec': sub.lec,
                            'lab': sub.lab,
                            'total': sub.total,
                            'grade': sub.grade,
                        })
                    sems.append({'id': s.id, 'order': s.order, 'label': s.label, 'subjects': subs})
                years.append({'id': y.id, 'order': y.order, 'label': y.label, 'semesters': sems})
            # include assignments
            assigns = []
            for a in p.assignments.all():
                assigns.append({'id': a.id, 'program_name': a.program_name, 'program_code': a.program_code, 'intake_year': a.intake_year})
            out.append({'id': p.id, 'name': p.name, 'description': p.description, 'program_name': p.program_name, 'program_code': p.program_code, 'years': years, 'assignments': assigns})
        return JsonResponse({'success': True, 'data': out})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def list_programs(request):
    """Return list of Program records."""
    try:
        qs = Program.objects.all().order_by('name')
        data = [{'id': p.id, 'name': p.name, 'code': p.code} for p in qs]
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def create_prospectus(request):
    """Create a prospectus with nested years/semesters/subjects."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        program_name = data.get('program_name', '').strip()
        program_code = data.get('program_code', '').strip()
        years = data.get('years') or data.get('structure') or []

        # If a program name was provided, attempt to resolve program_code from Program table
        if program_name and not program_code:
            try:
                prog = Program.objects.filter(name__iexact=program_name).first()
                if prog:
                    program_code = prog.code or program_code
            except Exception:
                pass

        if not name:
            return JsonResponse({'success': False, 'message': 'Prospectus name is required.'}, status=400)

        p = Prospectus.objects.create(name=name, description=description, program_name=program_name, program_code=program_code, created_by=request.user)

        for y_idx, y in enumerate(years):
            y_label = y.get('label', f'Year {y_idx+1}')
            py = ProspectusYear.objects.create(prospectus=p, order=y_idx, label=y_label)
            for s_idx, s in enumerate(y.get('semesters', [])):
                s_label = s.get('label', f'Semester {s_idx+1}')
                ps = ProspectusSemester.objects.create(year=py, order=s_idx, label=s_label)
                for sub_idx, sub in enumerate(s.get('subjects', [])):
                    ProspectusSubject.objects.create(
                        semester=ps,
                        order=sub_idx,
                        code=sub.get('code','').strip(),
                        title=sub.get('title','').strip() or 'Untitled',
                        prereq=sub.get('prereq','').strip(),
                        lec=int(sub.get('lec') or 0),
                        lab=int(sub.get('lab') or 0),
                        total=int(sub.get('total') or 0),
                        grade=str(sub.get('grade') or '').strip()
                    )

        AdminActivityLog.objects.create(admin=request.user, action='created_prospectus', notes=f'Created prospectus: {p.name}')

        return JsonResponse({'success': True, 'message': 'Prospectus created.', 'id': p.id})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_prospectus(request, prospectus_id=None):
    try:
        data = json.loads(request.body) if request.body else {}
        pid = prospectus_id or data.get('id')
        if not pid:
            return JsonResponse({'success': False, 'message': 'Prospectus id required.'}, status=400)
        p = Prospectus.objects.get(id=pid)
        name = p.name
        p.delete()
        AdminActivityLog.objects.create(admin=request.user, action='deleted_prospectus', notes=f'Deleted prospectus: {name}')
        return JsonResponse({'success': True, 'message': 'Prospectus deleted.'})
    except Prospectus.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prospectus not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def assign_prospectus(request):
    """Assign a prospectus to a program/intake."""
    try:
        data = json.loads(request.body)
        prospectus_id = data.get('prospectus_id')
        program_name = data.get('program_name', '').strip()
        program_code = data.get('program_code', '').strip()
        intake_year = data.get('intake_year', '').strip()

        if not prospectus_id:
            return JsonResponse({'success': False, 'message': 'prospectus_id is required.'}, status=400)
        p = Prospectus.objects.get(id=prospectus_id)
        # Update existing assignment or create
        assignment, created = ProspectusAssignment.objects.update_or_create(
            program_name=program_name,
            intake_year=intake_year,
            defaults={'prospectus': p, 'program_code': program_code}
        )
        AdminActivityLog.objects.create(admin=request.user, action='assigned_prospectus', notes=f'Assigned {p.name} to {program_name} {intake_year}')
        return JsonResponse({'success': True, 'message': 'Assigned prospectus.', 'assignment_id': assignment.id})
    except Prospectus.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Prospectus not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def add_student_requirement(request):
    """Add a missing requirement for a student."""
    from ..models import StudentRequirement, RequirementType, RequirementNotification
    from django.contrib.auth.models import User

    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        requirement_id = data.get('requirement_id')
        notes = data.get('notes', '').strip()

        if not user_id or not requirement_id:
            return JsonResponse({'success': False, 'message': 'User ID and Requirement ID are required.'}, status=400)

        user = User.objects.get(id=user_id)
        requirement = RequirementType.objects.get(id=requirement_id)

        # Check if already exists
        if StudentRequirement.objects.filter(user=user, requirement=requirement).exists():
            return JsonResponse({'success': False, 'message': 'This requirement is already marked for this student.'}, status=400)

        student_req = StudentRequirement.objects.create(
            user=user,
            requirement=requirement,
            notes=notes,
            status='pending'
        )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=Application.objects.filter(user=user).first(),
            notes=f"Added missing requirement for {user.username}: {requirement.name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Requirement added successfully.',
            'data': {
                'id': student_req.id,
                'requirement_name': requirement.name,
                'status': student_req.status
            }
        })
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'User not found.'}, status=404)
    except RequirementType.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Requirement type not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def remove_student_requirement(request):
    """Remove a missing requirement from a student."""
    from ..models import StudentRequirement

    try:
        data = json.loads(request.body)
        requirement_id = data.get('student_requirement_id')

        if not requirement_id:
            return JsonResponse({'success': False, 'message': 'Student requirement ID is required.'}, status=400)

        student_req = StudentRequirement.objects.get(id=requirement_id)
        user = student_req.user
        req_name = student_req.requirement.name
        student_req.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=Application.objects.filter(user=user).first(),
            notes=f"Removed missing requirement for {user.username}: {req_name}"
        )

        return JsonResponse({'success': True, 'message': 'Requirement removed successfully.'})
    except StudentRequirement.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student requirement not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_student_requirement_status(request):
    """Update the status of a student requirement."""
    from ..models import StudentRequirement

    try:
        data = json.loads(request.body)
        requirement_id = data.get('student_requirement_id')
        new_status = data.get('status')

        if not requirement_id or not new_status:
            return JsonResponse({'success': False, 'message': 'Requirement ID and status are required.'}, status=400)

        valid_statuses = ['pending', 'notified', 'submitted', 'waived']
        if new_status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status.'}, status=400)

        student_req = StudentRequirement.objects.get(id=requirement_id)
        old_status = student_req.status
        student_req.status = new_status

        if new_status == 'notified':
            student_req.notified_at = timezone.now()

        student_req.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            application=Application.objects.filter(
                user=student_req.user).first(),
            notes=f"Updated requirement status for {student_req.user.username}: {student_req.requirement.name} ({old_status} -> {new_status})"
        )

        return JsonResponse({
            'success': True,
            'message': 'Status updated successfully.',
            'data': {'status': student_req.status}
        })
    except StudentRequirement.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Student requirement not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def send_requirement_notification(request):
    """Send a notification to a student about missing requirements."""
    from ..models import StudentRequirement, RequirementNotification
    from django.core.mail import send_mail
    from django.conf import settings

    try:
        data = json.loads(request.body)
        student_requirement_ids = data.get('student_requirement_ids', [])
        message = data.get('message', '').strip()

        if not student_requirement_ids:
            return JsonResponse({'success': False, 'message': 'At least one student requirement is required.'}, status=400)

        if not message:
            return JsonResponse({'success': False, 'message': 'Notification message is required.'}, status=400)

        # Group requirements by user
        requirements_by_user = {}
        for req_id in student_requirement_ids:
            try:
                req = StudentRequirement.objects.get(id=req_id)
                user_id = req.user.id
                if user_id not in requirements_by_user:
                    requirements_by_user[user_id] = {
                        'user': req.user,
                        'requirements': [],
                        'req_ids': []
                    }
                requirements_by_user[user_id]['requirements'].append(
                    req.requirement.name)
                requirements_by_user[user_id]['req_ids'].append(req_id)
            except StudentRequirement.DoesNotExist:
                continue

        # Send notifications to each student
        notifications_sent = 0
        for user_id, user_data in requirements_by_user.items():
            user = user_data['user']
            req_names = ', '.join(user_data['requirements'])

            # Update status to notified
            for req_id in user_data['req_ids']:
                StudentRequirement.objects.filter(id=req_id).update(
                    status='notified',
                    notified_at=timezone.now()
                )

            # Create notification record
            for req_id in user_data['req_ids']:
                RequirementNotification.objects.create(
                    student_requirement_id=req_id,
                    sent_by=request.user,
                    message=f"{message}\n\nMissing requirements: {req_names}"
                )

            # Send email notification
            try:
                full_name = user.get_full_name() or user.email
                email_message = f"""Dear {full_name},

{message}

Missing Requirements:
- {req_names}

Please submit the required documents as soon as possible.

Best regards,
Admissions Office
"""
                send_mail(
                    subject='Action Required: Missing Admission Requirements',
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                notifications_sent += 1
            except Exception as e:
                # Log but continue with other students
                print(f"Failed to send email to {user.email}: {e}")

        AdminActivityLog.objects.create(
            admin=request.user,
            action='note',
            notes=f"Sent {notifications_sent} requirement notifications to students."
        )

        return JsonResponse({
            'success': True,
            'message': f'Notifications sent to {notifications_sent} student(s).'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_all_students(request):
    """Get list of all students with applications for selection."""
    from django.contrib.auth.models import User
    from students_app.models import PersonalDetails

    users = User.objects.filter(
        application__isnull=False
    ).select_related('application').distinct().order_by('username')

    data = []
    for user in users:
        # Get personal details if available
        personal = PersonalDetails.objects.filter(user=user).first()
        full_name = personal.first_name + ' ' + \
            personal.last_name if personal else user.get_full_name() or user.email

        app = Application.objects.filter(user=user).first()

        data.append({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': full_name,
            'application_id': app.application_id if app else None,
            'program': app.program if app else None
        })

    return JsonResponse({'success': True, 'data': data})


# ============== Program CMS APIs ==============

@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_program_cms(request):
    """Get all program CMS data."""
    from ..models import CMSSettings, Faculty

    try:
        cms = CMSSettings.objects.get(pk=1)
    except CMSSettings.DoesNotExist:
        CMSSettings.objects.create(pk=1)
        cms = CMSSettings.objects.get(pk=1)

    # Get faculty members
    faculty_list = Faculty.objects.filter(is_active=True).order_by('order')
    faculties = [{
        'id': f.id,
        'first_name': f.first_name,
        'last_name': f.last_name,
        'title': f.title,
        'specializations': f.specializations,
        'photo': f.photo.url if f.photo else None,
        'order': f.order,
    } for f in faculty_list]

    data = {
        'program_name': cms.program_name,
        'program_degree': cms.program_degree,
        'program_title': cms.program_title,
        'program_tagline': cms.program_tagline,
        'program_description': cms.program_description,
        'program_institution': cms.program_institution,
        'program_copc_number': cms.program_copc_number,
        'program_effective_year': cms.program_effective_year,
        'program_accreditor': cms.program_accreditor,
        'program_objectives': cms.program_objectives,
        'program_outcomes': cms.program_outcomes,
        'program_curriculum': cms.program_curriculum,
        'program_stats': cms.program_stats,
        'faculties': faculties,
    }

    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_program_cms(request):
    """Update program CMS settings."""
    from ..models import CMSSettings

    try:
        data = json.loads(request.body)

        # Get or create CMS settings
        try:
            cms = CMSSettings.objects.get(pk=1)
        except CMSSettings.DoesNotExist:
            CMSSettings.objects.create(pk=1)
            cms = CMSSettings.objects.get(pk=1)

        # Update program basic info
        cms.program_name = data.get('program_name', cms.program_name).strip()
        cms.program_degree = data.get(
            'program_degree', cms.program_degree).strip()
        cms.program_title = data.get(
            'program_title', cms.program_title).strip()
        cms.program_tagline = data.get(
            'program_tagline', cms.program_tagline).strip()
        cms.program_description = data.get(
            'program_description', cms.program_description).strip()
        cms.program_institution = data.get(
            'program_institution', cms.program_institution).strip()
        cms.program_copc_number = data.get(
            'program_copc_number', cms.program_copc_number).strip()
        cms.program_effective_year = data.get(
            'program_effective_year', cms.program_effective_year).strip()
        cms.program_accreditor = data.get(
            'program_accreditor', cms.program_accreditor).strip()

        # Update objectives [{title, description}]
        objectives = data.get('program_objectives', None)
        if objectives is not None:
            cleaned_objectives = []
            for obj in objectives:
                title = str(obj.get('title', '')).strip()
                description = str(obj.get('description', '')).strip()
                if title:
                    cleaned_objectives.append(
                        {'title': title, 'description': description})
            cms.program_objectives = cleaned_objectives

        # Update outcomes [{number, title, description}]
        outcomes = data.get('program_outcomes', None)
        if outcomes is not None:
            cleaned_outcomes = []
            for outcome in outcomes:
                try:
                    number = int(outcome.get('number', 0))
                except (ValueError, TypeError):
                    number = 0
                title = str(outcome.get('title', '')).strip()
                description = str(outcome.get('description', '')).strip()
                if title and number > 0:
                    cleaned_outcomes.append({
                        'number': number,
                        'title': title,
                        'description': description
                    })
            cms.program_outcomes = cleaned_outcomes

        # Update curriculum [{title, courses: [{code, name, units}]}]
        curriculum = data.get('program_curriculum', None)
        if curriculum is not None:
            cleaned_curriculum = []
            for group in curriculum:
                group_title = str(group.get('title', '')).strip()
                courses_raw = group.get('courses', [])
                cleaned_courses = []
                for course in courses_raw:
                    code = str(course.get('code', '')).strip()
                    name = str(course.get('name', '')).strip()
                    try:
                        units = int(course.get('units', 0))
                    except (ValueError, TypeError):
                        units = 0
                    if code and name and units > 0:
                        cleaned_courses.append({
                            'code': code,
                            'name': name,
                            'units': units
                        })
                if group_title and cleaned_courses:
                    cleaned_curriculum.append({
                        'title': group_title,
                        'courses': cleaned_courses
                    })
            cms.program_curriculum = cleaned_curriculum

        # Update stats [{stat_label, stat_value}]
        stats = data.get('program_stats', None)
        if stats is not None:
            cleaned_stats = []
            for stat in stats:
                label = str(stat.get('stat_label', '')).strip()
                value = str(stat.get('stat_value', '')).strip()
                if label and value:
                    cleaned_stats.append({
                        'stat_label': label,
                        'stat_value': value
                    })
            cms.program_stats = cleaned_stats

        cms.save()

        # Log the activity
        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Program CMS settings updated.'
        )

        return JsonResponse({'success': True, 'message': 'Program CMS settings updated successfully.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["GET"])
def get_faculty_list(request):
    """Get list of all faculty members."""
    from ..models import Faculty

    faculty = Faculty.objects.filter(is_active=True).order_by('order')
    data = [{
        'id': f.id,
        'first_name': f.first_name,
        'last_name': f.last_name,
        'title': f.title,
        'specializations': f.specializations,
        'photo': f.photo.url if f.photo else None,
        'order': f.order,
    } for f in faculty]

    return JsonResponse({'success': True, 'data': data})


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def add_faculty_member(request):
    """Add a new faculty member."""
    from ..models import Faculty

    try:
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        title = request.POST.get('title', '').strip()
        specializations = request.POST.get('specializations', '').strip()
        photo = request.FILES.get('photo', None)

        if not first_name or not last_name or not title:
            return JsonResponse({
                'success': False,
                'message': 'First name, last name, and title are required.'
            }, status=400)

        # Validate photo if provided
        if photo:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if photo.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': 'Only JPG, PNG, and WEBP images are allowed.'
                }, status=400)

            max_size = 5 * 1024 * 1024  # 5MB
            if photo.size > max_size:
                return JsonResponse({
                    'success': False,
                    'message': 'Photo size must not exceed 5MB.'
                }, status=400)

        # Get next order number
        last_faculty = Faculty.objects.order_by('-order').first()
        next_order = (last_faculty.order + 1) if last_faculty else 1

        faculty = Faculty.objects.create(
            first_name=first_name,
            last_name=last_name,
            title=title,
            specializations=specializations,
            photo=photo if photo else None,
            order=next_order
        )

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f"Added faculty member: {first_name} {last_name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty member added successfully.',
            'data': {
                'id': faculty.id,
                'first_name': faculty.first_name,
                'last_name': faculty.last_name,
                'title': faculty.title,
                'specializations': faculty.specializations,
                'photo': faculty.photo.url if faculty.photo else None,
                'order': faculty.order,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def update_faculty_member(request):
    """Update an existing faculty member."""
    from ..models import Faculty

    try:
        faculty_id = request.POST.get('faculty_id')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        title = request.POST.get('title', '').strip()
        specializations = request.POST.get('specializations', '').strip()
        photo = request.FILES.get('photo', None)

        if not faculty_id:
            return JsonResponse({
                'success': False,
                'message': 'Faculty ID is required.'
            }, status=400)

        faculty = Faculty.objects.get(id=faculty_id)

        # Update fields if provided
        if first_name:
            faculty.first_name = first_name
        if last_name:
            faculty.last_name = last_name
        if title:
            faculty.title = title

        faculty.specializations = specializations

        # Update photo if provided
        if photo:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if photo.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': 'Only JPG, PNG, and WEBP images are allowed.'
                }, status=400)

            max_size = 5 * 1024 * 1024  # 5MB
            if photo.size > max_size:
                return JsonResponse({
                    'success': False,
                    'message': 'Photo size must not exceed 5MB.'
                }, status=400)

            # Delete old photo if exists
            if faculty.photo:
                if default_storage.exists(faculty.photo.name):
                    default_storage.delete(faculty.photo.name)

            faculty.photo = photo

        faculty.save()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f"Updated faculty member: {faculty.first_name} {faculty.last_name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty member updated successfully.',
            'data': {
                'id': faculty.id,
                'first_name': faculty.first_name,
                'last_name': faculty.last_name,
                'title': faculty.title,
                'specializations': faculty.specializations,
                'photo': faculty.photo.url if faculty.photo else None,
                'order': faculty.order,
            }
        })
    except Faculty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Faculty member not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def delete_faculty_member(request):
    """Delete a faculty member."""
    from ..models import Faculty

    try:
        data = json.loads(request.body)
        faculty_id = data.get('faculty_id')

        if not faculty_id:
            return JsonResponse({
                'success': False,
                'message': 'Faculty ID is required.'
            }, status=400)

        faculty = Faculty.objects.get(id=faculty_id)
        full_name = faculty.get_full_name()

        # Delete photo if exists
        if faculty.photo:
            if default_storage.exists(faculty.photo.name):
                default_storage.delete(faculty.photo.name)

        faculty.delete()

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes=f"Deleted faculty member: {full_name}"
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty member deleted successfully.'
        })
    except Faculty.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Faculty member not found.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
@require_http_methods(["POST"])
def reorder_faculty(request):
    """Reorder faculty members."""
    from ..models import Faculty

    try:
        data = json.loads(request.body)
        faculty_orders = data.get('faculty_orders', [])

        for item in faculty_orders:
            faculty_id = item.get('id')
            order = item.get('order')

            try:
                faculty = Faculty.objects.get(id=faculty_id)
                faculty.order = order
                faculty.save()
            except Faculty.DoesNotExist:
                continue

        AdminActivityLog.objects.create(
            admin=request.user,
            action='cms_updated',
            notes='Reordered faculty members.'
        )

        return JsonResponse({
            'success': True,
            'message': 'Faculty members reordered successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
