from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import secrets
import hashlib

from recordkeeping_proj.emailjs import send_email_via_emailjs
from students_app.models import UserProfile


def generate_verification_token(email):
    """Generate a unique verification token for the user."""
    # Create a secure token using email + random bytes
    random_bytes = secrets.token_hex(32)
    token_string = f"{email}:{random_bytes}"
    # Hash it for security
    token = hashlib.sha256(token_string.encode()).hexdigest()
    return token


def send_verification_email(request, user, token):
    """Send email verification link to user via EmailJS."""
    verification_url = request.build_absolute_uri(f'/verify/{token}/')
    template_id = getattr(settings, "EMAILJS_TEMPLATE_VERIFICATION", "")
    student_name = f"{user.first_name} {user.last_name}".strip() or user.email
    template_params = {
        "to_email": user.email,
        "student_name": student_name,
        "verification_link": verification_url,
    }
    ok, err = send_email_via_emailjs(template_id, template_params)
    if not ok:
        print(f"Error sending verification email: {err}")
    return ok


def signup_view(request):
    """
    Handle user registration.
    - For regular users (students): is_staff=False, is_superuser=False
    - For admins: is_staff=True, is_superuser=True
    
    Email verification is required for all users.
    """
    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        role = request.POST.get('role', 'student')  # Default is student

        # Validation
        if not first_name or not last_name or not email or not password:
            messages.error(request, 'All fields are required.')
            return render(request, 'students_app/register.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'students_app/register.html')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'students_app/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')
            return render(request, 'students_app/register.html')

        try:
            # Generate verification token
            verification_token = generate_verification_token(email)
            
            # Create user based on role - set is_active=False until email is verified
            if role == 'admin':
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,    # Admin can access admin site
                    is_superuser=True, # Admin has full permissions
                    is_active=True     # Admins are auto-active (can be changed to False)
                )
            else:
                # Student role (default) - require email verification
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=False,
                    is_superuser=False,
                    is_active=False  # User is inactive until email is verified
                )

            # Create UserProfile with verification token
            UserProfile.objects.create(
                user=user,
                verification_token=verification_token,
                token_created_at=timezone.now(),
                is_email_verified=False
            )

            # Send verification email
            if send_verification_email(request, user, verification_token):
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
            else:
                # If email fails, still show success but with warning
                messages.warning(request, 'Registration successful! However, we could not send the verification email. Please contact support.')
            
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'students_app/register.html')

    # If GET request, show the registration form
    return render(request, 'students_app/register.html')

