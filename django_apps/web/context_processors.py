"""Template context processors for the web app."""

from django.conf import settings
from django.http import HttpRequest


def django_debug(_request: HttpRequest) -> dict[str, bool]:
    """Expose ``settings.DEBUG`` for templates (e.g. safe dev-only UI)."""
    return {"DJANGO_DEBUG": settings.DEBUG}
