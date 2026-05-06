"""Template context processors for the web app."""

import os

from django.conf import settings
from django.http import HttpRequest


def django_debug(_request: HttpRequest) -> dict[str, bool]:
    """Expose ``settings.DEBUG`` for templates (e.g. safe dev-only UI)."""
    return {"DJANGO_DEBUG": settings.DEBUG}


def google_social_login_enabled(_request: HttpRequest) -> dict[str, bool]:
    """True when Google OAuth works: env id+secret (see settings) or SocialApp for SITE_ID."""
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    sec = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    if cid and sec:
        return {"google_social_login_enabled": True}
    # Admin-created Social applications (no env vars).
    from allauth.socialaccount.models import SocialApp

    site_id = getattr(settings, "SITE_ID", 1)
    enabled = SocialApp.objects.filter(provider="google", sites__id=site_id).exists()
    return {"google_social_login_enabled": enabled}
