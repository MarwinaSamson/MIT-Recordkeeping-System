from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

from students_app.models import UserProfile


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
                # Redirect to personal details after successful login
                return redirect('personalDetails')
            else:
                messages.error(request, 'Your account is inactive.')
        else:
            messages.error(request, 'Invalid email or password.')

        return render(request, "students_app/login.html")

    return render(request, "students_app/login.html")
