from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden


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
    Displays the main admin dashboard with navigation.
    """
    context = {
        'page_title': 'Admin Dashboard',
        'admin_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'admin_app/admin_dashboard.html', context)
