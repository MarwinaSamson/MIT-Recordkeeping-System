from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.http import HttpResponseForbidden
import json
from ..utils import (
    get_applications_summary,
    get_recent_applications,
    get_verification_progress,
    get_activity_log,
)
from ..models import Application, AdminProfile, CMSSettings
from .document_verification import _build_application_list


# Friendly labels for document types when the model does not define choices



def is_superuser(user):
    """
    Test function to check if the user is a superuser.
    Returns True only if user is authenticated and is a superuser.
    """
    return user.is_superuser


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def admin_dashboard(request):
    """
    Admin dashboard view.
    Only accessible to superusers (is_superuser=True in auth_user table).
    Displays the main admin dashboard with real data from database.
    """
    # Get all applications for document verification section
    all_applications = _build_application_list()

    # Get all activities for activity history section
    all_activities = get_activity_log(limit=100)

    # Get admin profile picture
    admin_profile_picture = None
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
        if admin_profile.profile_picture:
            admin_profile_picture = admin_profile.profile_picture.url
    except AdminProfile.DoesNotExist:
        pass

    cms_obj = CMSSettings.objects.filter(pk=1).first()
    if not cms_obj:
        cms_obj = CMSSettings(pk=1)
        cms_obj.save()

    context = {
        'page_title': 'Admin Dashboard',
        'admin_name': request.user.get_full_name() or request.user.username,
        'admin_email': request.user.email,
        'admin_profile_picture': admin_profile_picture,
        # Dashboard statistics
        'summary': get_applications_summary(),
        'recent_applications': get_recent_applications(limit=5),
        'verification_progress': get_verification_progress(),
        'recent_activities': get_activity_log(limit=10),
        # CMS settings for homepage
        'cms': cms_obj,
        'all_applications': json.dumps(all_applications),
        'all_activities': json.dumps(all_activities),
    }
    return render(request, 'admin_app/admin_dashboard.html', context)


@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def logout_admin(request):
    """
    Logout the admin user and redirect to login page.
    """
    logout(request)
    return redirect('login')



@login_required(login_url='login')
@user_passes_test(is_superuser, login_url='login')
def program_management(request):
    # Get admin profile picture
    admin_profile_picture = None
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
        if admin_profile.profile_picture:
            admin_profile_picture = admin_profile.profile_picture.url
    except AdminProfile.DoesNotExist:
        pass

    context = {
        'page_title': 'Program Management',
        'admin_name': request.user.get_full_name() or request.user.username,
        'admin_email': request.user.email,
        'admin_profile_picture': admin_profile_picture,
        'current_user_id': request.user.id,
    }
    return render(request, 'admin_app/program_management.html', context)