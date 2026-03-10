from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages


def signup_view(request):
    """
    Handle user registration.
    - For regular users (students): is_staff=False, is_superuser=False
    - For admins: is_staff=True, is_superuser=True
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
            # Create user based on role
            if role == 'admin':
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=True,    # Admin can access admin site
                    is_superuser=True, # Admin has full permissions
                    is_active=True
                )
            else:
                # Student role (default)
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_staff=False,
                    is_superuser=False,
                    is_active=True
                )

            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')

        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'students_app/register.html')

    # If GET request, show the registration form
    return render(request, 'students_app/register.html')

