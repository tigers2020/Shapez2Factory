"""Template tags for language-prefixed URLs (used with i18n_patterns)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)  # type: ignore[untyped-decorator]
def url_for_language(context: Mapping[str, Any], lang_code: str) -> str:
    """Return the current request path translated to ``lang_code`` for set_language ``next``."""
    request = context.get("request")
    if request is None:
        return "/"
    return cast(str, translate_url(request.path, lang_code))
