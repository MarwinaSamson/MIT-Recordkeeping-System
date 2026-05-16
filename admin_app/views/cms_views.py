"""
cms_views.py
─────────────────────────────────────────────────────────────────────────────
View for the dedicated CMS Settings page (cms_settings.html).
Add this to your admin_app/views/ folder and register it in urls.py.

USAGE in urls.py:
    from .views.cms_views import cms_settings

    urlpatterns = [
        ...
        path('settings/', cms_settings, name='cms_settings'),
        ...
    ]
─────────────────────────────────────────────────────────────────────────────
"""

import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.utils import timezone
from datetime import timedelta

from ..models import AdminProfile, CMSSettings, AdminActivityLog, SchoolYear
from ..utils import get_activity_log   # reuse existing helper

LOG_RETENTION_DAYS = 90

# Curriculum groups shown on the About page Courses tab — ensures the CMS UI
# always has selectable groups even on a fresh install (program_curriculum was []).
_DEFAULT_PROGRAM_CURRICULUM = [
    {"title": "Core Courses", "courses": []},
    {"title": "Specialization", "courses": []},
    {"title": "Capstone", "courses": []},
]


def is_superuser(user):
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def cms_settings(request):
    """
    Dedicated CMS / Settings page view.
    Renders cms_settings.html with all data the template needs.
    """

    # ── Admin profile picture ──────────────────────────────────────────────
    admin_profile_picture = None
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
        if admin_profile.profile_picture:
            admin_profile_picture = admin_profile.profile_picture.url
    except AdminProfile.DoesNotExist:
        pass

    # ── CMS singleton ──────────────────────────────────────────────────────
    cms = CMSSettings.objects.filter(pk=1).first()
    if not cms:
        cms = CMSSettings(pk=1)
        cms.save()

    cur = cms.program_curriculum
    if not cur or not isinstance(cur, list) or len(cur) == 0:
        cms.program_curriculum = [
            {"title": g["title"], "courses": list(g["courses"])}
            for g in _DEFAULT_PROGRAM_CURRICULUM
        ]
        CMSSettings.objects.filter(pk=cms.pk).update(
            program_curriculum=cms.program_curriculum
        )

    # ── Auto-cleanup: delete activity logs older than retention period ───────
    cutoff = timezone.now() - timedelta(days=LOG_RETENTION_DAYS)
    AdminActivityLog.objects.filter(timestamp__lt=cutoff).delete()

    # ── Active school year (shown in header) ──────────────────────────────
    active_school_year = SchoolYear.objects.filter(is_active=True).first()

    # ── Recent activity log (for History Logs tab) ─────────────────────────
    all_activities = get_activity_log(limit=200)

    context = {
        'page_title':             'CMS Settings',
        'admin_name':             request.user.get_full_name() or request.user.username,
        'admin_email':            request.user.email,
        'admin_profile_picture':  admin_profile_picture,

        # CMS data consumed by the template
        'cms':                    cms,

        # Active school year shown in header
        'active_school_year':     active_school_year,

        # Serialised activity log for the History Logs tab
        'all_activities':         json.dumps(all_activities),
    }

    return render(request, 'admin_app/cms_settings.html', context)
