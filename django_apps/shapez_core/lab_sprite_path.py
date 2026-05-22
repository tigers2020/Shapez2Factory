"""Resolve lab SVG path under ``web/assets/sprites/`` for a basedata identifier ``value``."""

from __future__ import annotations

from pathlib import Path

# Blueprint ``T`` strings that share art with another committed identifier.
LAB_SPRITE_IDENTIFIER_ALIASES: dict[str, str] = {
    "Layout_ProMiner": "Layout_ShapeMiner",
    "SpaceBelt_Left": "SpaceBelt_LeftTurn",
    "SpacePipe_Left": "SpacePipe_LeftTurn",
    "SpaceBelt_Right": "SpaceBelt_RightTurn",
    "SpacePipe_Right": "SpacePipe_RightTurn",
}


def default_lab_sprites_root() -> Path:
    """``django_apps/web/static/web/assets/sprites`` (repo layout)."""

    return Path(__file__).resolve().parent.parent / "web" / "static" / "web" / "assets" / "sprites"


def _relpath_for_identifier_at_root(identifier_value: str, root: Path) -> str:
    """Return posix relpath when ``identifier_value.svg`` exists under ``root`` rules."""

    v = identifier_value.strip()
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
        rel = basename
    if (root / rel).is_file():
        return rel
    return ""


def resolve_sprite_static_relpath(
    identifier_value: str,
    *,
    sprites_root: Path | None = None,
) -> str:
    """Return posix relpath under static ``web/assets/sprites/``, or ``""`` if no file.

    Tries ``identifier_value`` then :data:`LAB_SPRITE_IDENTIFIER_ALIASES` targets.
    """

    root = sprites_root if sprites_root is not None else default_lab_sprites_root()
    v = (identifier_value or "").strip()
    if not v:
        return ""
    candidates = [v]
    alias = LAB_SPRITE_IDENTIFIER_ALIASES.get(v)
    if alias and alias not in candidates:
        candidates.append(alias)
    for cand in candidates:
        rel = _relpath_for_identifier_at_root(cand, root)
        if rel:
            return rel
    return ""


def scan_committed_lab_sprite_identifier_map(
    *,
    sprites_root: Path | None = None,
) -> dict[str, str]:
    """Map blueprint ``T`` → posix relpath for every committed SVG under ``sprites/``."""

    root = sprites_root if sprites_root is not None else default_lab_sprites_root()
    out: dict[str, str] = {}
    for subdir in ("SpaceBelt", "SpacePipe", "Miner"):
        folder = root / subdir
        if not folder.is_dir():
            continue
        for path in folder.glob("*.svg"):
            out[path.stem] = f"{subdir}/{path.name}"
    for path in root.glob("*.svg"):
        out[path.stem] = path.name
    for alias, target in LAB_SPRITE_IDENTIFIER_ALIASES.items():
        if alias in out:
            continue
        rel = out.get(target) or _relpath_for_identifier_at_root(target, root)
        if rel:
            out[alias] = rel
    return out
