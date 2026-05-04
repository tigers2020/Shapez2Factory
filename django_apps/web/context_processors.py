"""Template context processors for the web app."""

from django.conf import settings


def django_debug(_request):
    """Expose ``settings.DEBUG`` for templates (e.g. safe dev-only UI)."""
    return {"DJANGO_DEBUG": settings.DEBUG}
