"""Resolve lab SVG path under ``web/assets/sprites/`` for a basedata identifier ``value``."""

from __future__ import annotations

from pathlib import Path


def default_lab_sprites_root() -> Path:
    """``django_apps/web/static/web/assets/sprites`` (repo layout)."""

    return Path(__file__).resolve().parent.parent / "web" / "static" / "web" / "assets" / "sprites"


def resolve_sprite_static_relpath(
    identifier_value: str,
    *,
    sprites_root: Path | None = None,
) -> str:
    """Return posix relpath under static ``web/assets/sprites/``, or ``""`` if no file.

    Convention (current repo assets):
    - ``SpacePipe_*`` → ``SpacePipe/<value>.svg``
    - ``SpaceBelt_*`` → ``SpaceBelt/<value>.svg``
    - ``Layout_*`` → ``Miner/<value>.svg`` (only committed miner/layout SVGs match)
    """

    root = sprites_root if sprites_root is not None else default_lab_sprites_root()
    v = (identifier_value or "").strip()
    if not v:
        return ""
    basename = f"{v}.svg"
    if v.startswith("SpacePipe_"):
        rel = f"SpacePipe/{basename}"
    elif v.startswith("SpaceBelt_"):
        rel = f"SpaceBelt/{basename}"
    elif v.startswith("Layout_"):
        rel = f"Miner/{basename}"
    else:
        return ""
    path = root / rel
    if path.is_file():
        return rel
    return ""
