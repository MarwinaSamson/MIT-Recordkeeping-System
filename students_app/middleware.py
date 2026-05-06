from datetime import datetime, timedelta, timezone as dt_timezone
from django.conf import settings

from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

class SessionSecurityMiddleware:
    """Ensure each account has only one active session and enforce inactivity timeout."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.process_request(request)
        if response:
            return response
        return self.get_response(request)

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        profile = getattr(request.user, 'profile', None)
        if profile is not None:
            if profile.current_session_key is None:
                profile.current_session_key = session_key
                profile.save(update_fields=['current_session_key'])
            elif profile.current_session_key != session_key:
                logout(request)
                request.session.flush()
                return redirect(reverse('index'))

        # inactivity timeout (minutes) — configurable from settings
        timeout_minutes = getattr(settings, 'SESSION_TIMEOUT_MINUTES', 60)
        last_activity = request.session.get('last_activity')
        if last_activity is not None:
            last_seen = datetime.fromtimestamp(last_activity, tz=dt_timezone.utc)
            if timezone.now() - last_seen > timedelta(minutes=timeout_minutes):
                logout(request)
                request.session.flush()
                return redirect(reverse('index'))

        request.session['last_activity'] = timezone.now().timestamp()
        return None
