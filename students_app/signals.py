from django.contrib.auth import logout
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone
from students_app.utils import get_user_redirect_url


@receiver(user_logged_in)
def ensure_single_active_session(sender, user, request, **kwargs):
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    profile = getattr(user, 'profile', None)
    if profile is None:
        return

    previous_session_key = profile.current_session_key
    if previous_session_key and previous_session_key != session_key:
        try:
            Session.objects.get(session_key=previous_session_key).delete()
        except Session.DoesNotExist:
            pass

    profile.current_session_key = session_key
    profile.save(update_fields=['current_session_key'])
    request.session['last_activity'] = timezone.now().timestamp()
    
    # Store the correct redirect URL in the session for SSO login
    redirect_url = get_user_redirect_url(user)
    request.session['_redirect_after_login'] = redirect_url


@receiver(user_logged_out)
def clear_current_session_key(sender, user, request, **kwargs):
    profile = getattr(user, 'profile', None)
    if profile is None:
        return

    current_session_key = request.session.session_key
    if current_session_key and profile.current_session_key == current_session_key:
        profile.current_session_key = None
        profile.save(update_fields=['current_session_key'])
