from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from ..models import PrivacyConsent


@login_required
def privacy_notice(request):
    if request.method == "POST":
        agreed = request.POST.get("agreeCheckbox") == "on"
        if not agreed:
            messages.error(request, "You must agree to the privacy notice to proceed.")
            return render(request, "students_app/privacyNotice.html")

        user = request.user

        consent, created = PrivacyConsent.objects.get_or_create(user=user)
        consent.agreed = True
        consent.name = "{user.first_name} {user.last_name}".strip() or ""
        consent.signed_at = timezone.now()
        consent.user_agent = request.META.get("HTTP_USER_AGENT", "")
        consent.ip_address = request.META.get("REMOTE_ADDR", "")
        consent.form_version = "1.0"
        consent.save()

        messages.success(request, "Privacy Notice agreement recorded.")
        return redirect("review")

    return render(request, "students_app/privacyNotice.html")
