from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from students_app.models import UserProfile


def verify_email_view(request, token):
    """
    Handle email verification.
    Validates the token and activates the user account.
    """
    try:
        # Find the user profile with this token
        user_profile = UserProfile.objects.get(verification_token=token)
        
        # Check if token has expired (24 hours validity)
        if user_profile.token_created_at:
            expiry_time = user_profile.token_created_at + timedelta(hours=24)
            if timezone.now() > expiry_time:
                # Token expired - delete the profile and user to allow re-registration
                user = user_profile.user
                user_profile.delete()
                user.delete()
                messages.error(request, 'Verification link has expired. Please register again.')
                return render(request, 'students_app/login.html')
        
        # Verify the email
        user = user_profile.user
        user.is_active = True
        user.save()
        
        # Update profile
        user_profile.is_email_verified = True
        user_profile.verification_token = None
        user_profile.token_created_at = None
        user_profile.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('login')
        
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid verification link. Please register again.')
        return redirect('register')
    except Exception as e:
        messages.error(request, f'Error verifying email: {str(e)}')
        return redirect('login')

