from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_field
from django.contrib.auth import get_user_model
from students_app.utils import get_user_redirect_url

User = get_user_model()


class AccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for additional functionality.
    """
    pass


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to handle Google OAuth login.
    Automatically creates UserProfile and verifies email for Google users.
    Links existing accounts with same email.
    Handles correct redirect after SSO login based on application status.
    """

    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social login data.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get email from social login
        email = data.get('email')
        if email:
            user.email = email
        
        # Get first name and last name
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if first_name:
            user_field(user, 'first_name', first_name)
        if last_name:
            user_field(user, 'last_name', last_name)
            
        return user

    def pre_social_login(self, request, sociallogin):
        """
        Handle existing user linking by email.
        If a user with the same email exists, connect the social account to them.
        """
        if sociallogin.is_existing:
            return

        # Check if user with this email already exists
        try:
            email = sociallogin.account.extra_data.get('email')
            if email:
                existing_user = User.objects.get(email=email)
                sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass

    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and create UserProfile with email verified.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Create or get UserProfile for the user
        from students_app.models import UserProfile
        
        # Get the email from the social account
        email = sociallogin.account.extra_data.get('email', '')
        
        # Create UserProfile if it doesn't exist
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'is_email_verified': True,  # Google already verified the email
            }
        )
        
        # If profile exists but email not verified, verify it now
        if not created and not profile.is_email_verified:
            profile.is_email_verified = True
            profile.save()
        
        return user

    def get_login_redirect_url(self, request, sociallogin):
        """
        Determine the correct redirect URL for SSO login based on application status.
        Checks if user has completed application and redirects accordingly.
        """
        # User is already saved at this point, so we can check their status
        user = sociallogin.user
        redirect_url = get_user_redirect_url(user)
        return redirect_url

    def is_open_for_signup(self, request, sociallogin):
        """
        Allow signup for social accounts (Google).
        """
        return True