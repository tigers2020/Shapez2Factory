"""Admin HTML preview for ``ShapezGameIdentifier.sprite_static_relpath``."""

from __future__ import annotations

from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import SafeString


def identifier_sprite_admin_preview(
    relpath: str,
    *,
    img_px: int = 40,
    show_relpath: bool = False,
) -> SafeString | str:
    """Render sprite under ``web/assets/sprites/<relpath>`` or em dash when empty."""

    rel = (relpath or "").strip()
    if not rel:
        return "—"
    url = static(f"web/assets/sprites/{rel}")
    img = format_html(
        '<img src="{}" alt="" width="{}" height="{}" draggable="false" '
        'title="{}" style="display:block;object-fit:contain;background:#0f172a;" />',
        url,
        img_px,
        img_px,
        rel,
    )
    if not show_relpath:
        return img
    return format_html(
        '<div style="display:flex;align-items:center;gap:8px;">{}{}</div>',
        img,
        format_html('<code style="font-size:11px;">{}</code>', rel),
    )
