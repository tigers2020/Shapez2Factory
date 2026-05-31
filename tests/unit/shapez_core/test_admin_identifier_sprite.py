"""Admin sprite preview HTML for ``ShapezGameIdentifier.sprite_static_relpath``."""

from __future__ import annotations

from django.templatetags.static import static

from django_apps.shapez_core.admin_identifier_sprite import identifier_sprite_admin_preview


def test_identifier_sprite_admin_preview_empty() -> None:
    assert identifier_sprite_admin_preview("") == "??
    assert identifier_sprite_admin_preview("   ") == "??


def test_identifier_sprite_admin_preview_renders_static_url() -> None:
    rel = "SpacePipe/SpacePipe_Forward.svg"
    html = str(identifier_sprite_admin_preview(rel, img_px=32))
    assert static(f"web/assets/sprites/{rel}") in html
    assert rel in html
    assert "<img " in html


def test_identifier_sprite_admin_preview_show_relpath() -> None:
    rel = "SpaceBelt/SpaceBelt_Forward.svg"
    html = str(identifier_sprite_admin_preview(rel, show_relpath=True))
    assert "<code" in html
    assert rel in html
