from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from students_app.models import UserProfile
from students_app.utils import get_user_redirect_url


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, "students_app/login.html")

        # Authenticate using email as username
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                # Check if user has a profile (email verification)
                try:
                    profile = user.profile
                    if not profile.is_email_verified:
                        messages.error(request, 'Please verify your email address before logging in. Check your inbox for the verification link.')
                        return render(request, "students_app/login.html")
                except UserProfile.DoesNotExist:
                    # If no profile exists, allow login (for backwards compatibility)
                    pass
                
                login(request, user)
                # Determine redirect based on application status
                redirect_url = get_user_redirect_url(user)
                return redirect(redirect_url)
            else:
                messages.error(request, 'Your account is inactive.')
        else:
            messages.error(request, 'Invalid email or password.')

        return render(request, "students_app/login.html")

    return render(request, "students_app/login.html")


@login_required
def logout_view(request):
    # Clear all previous messages to avoid showing old login messages
    from django.contrib.messages.storage.fallback import FallbackStorage
    storage = FallbackStorage(request)
    for _ in storage:
        pass  # Iterate through all messages to clear them
    
    profile = getattr(request.user, 'profile', None)
    if profile is not None:
        current_session_key = request.session.session_key
        if current_session_key and profile.current_session_key == current_session_key:
            profile.current_session_key = None
            profile.save(update_fields=['current_session_key'])

    logout(request)
    messages.success(request, "You have signed out successfully. See you soon!")
    return redirect("index")
