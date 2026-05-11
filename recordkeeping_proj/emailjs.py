"""
Send mail through EmailJS REST API (https://www.emailjs.com/docs/rest-api/send/).

Configure templates in the EmailJS dashboard. Each template should set the
recipient address from a variable, for example To Email = {{to_email}}.

Expected template_params (names must match your template):
  - Verification: to_email, student_name, verification_link
  - Requirement notice: to_email, student_name, message, missing_requirements
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from django.conf import settings

EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def emailjs_ready() -> bool:
    return bool(
        getattr(settings, "EMAILJS_SERVICE_ID", "")
        and getattr(settings, "EMAILJS_PUBLIC_KEY", "")
    )


def send_email_via_emailjs(template_id: str, template_params: dict) -> tuple[bool, str | None]:
    """
    POST to EmailJS. Returns (success, error_message).
    """
    if not template_id:
        return False, "EmailJS template_id is empty"
    if not emailjs_ready():
        return False, "EmailJS is not configured (EMAILJS_SERVICE_ID / EMAILJS_PUBLIC_KEY)"

    payload = {
        "service_id": settings.EMAILJS_SERVICE_ID,
        "template_id": template_id,
        "user_id": settings.EMAILJS_PUBLIC_KEY,
        "template_params": template_params,
    }
    private_key = getattr(settings, "EMAILJS_PRIVATE_KEY", "") or ""
    if private_key:
        payload["accessToken"] = private_key

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        EMAILJS_API_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status == 200:
                return True, None
            body = resp.read().decode("utf-8", errors="replace")
            return False, f"Unexpected status {resp.status}: {body}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, f"HTTP {e.code}: {body}"
    except Exception as e:
        return False, str(e)
