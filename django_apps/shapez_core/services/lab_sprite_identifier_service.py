"""Lab map sprites: resolve static paths from ``ShapezGameIdentifier`` rows."""

from __future__ import annotations

from typing import cast

from django_apps.shapez_core.lab_sprite_path import scan_committed_lab_sprite_identifier_map
from django_apps.shapez_core.models import ShapezBasedataRelease, ShapezGameIdentifier


def resolve_lab_release_for_sprites(
    *, release_id: int | None = None
) -> ShapezBasedataRelease | None:
    """Latest :class:`ShapezBasedataRelease` by ``game_version``, or a specific ``release_id``."""

    if release_id is not None:
        return cast(
            ShapezBasedataRelease | None,
            ShapezBasedataRelease.objects.filter(pk=int(release_id)).first(),
        )
    return cast(
        ShapezBasedataRelease | None,
        ShapezBasedataRelease.objects.order_by("-game_version").first(),
    )


def get_lab_sprite_relpath_for_value(value: str, *, release_id: int | None = None) -> str:
    """Return ``sprite_static_relpath`` (posix under ``web/assets/sprites/``) or ``\"\"``.

    When ``release_id`` is omitted, pick the row for this ``T`` on the **highest** ``game_version``
    release that has a non-empty lab sprite path (so a newer sparse import does not shadow assets).
    """

    v = (value or "").strip()
    if not v:
        return ""
    qs = ShapezGameIdentifier.objects.exclude(sprite_static_relpath="").filter(value=v)
    if release_id is not None:
        qs = qs.filter(release_id=int(release_id))
    row = (
        qs.select_related("release")
        .order_by("-release__game_version")
        .values_list("sprite_static_relpath", flat=True)
        .first()
    )
    if row:
        return str(row)
    qs2 = ShapezGameIdentifier.objects.exclude(sprite_static_relpath="").filter(normalized_value=v)
    if release_id is not None:
        qs2 = qs2.filter(release_id=int(release_id))
    row = (
        qs2.select_related("release")
        .order_by("-release__game_version")
        .values_list("sprite_static_relpath", flat=True)
        .first()
    )
    return str(row) if row else ""


def build_lab_identifier_sprite_relpath_map(*, release_id: int | None = None) -> dict[str, str]:
    """Map blueprint ``T`` (:attr:`ShapezGameIdentifier.value`) → ``sprite_static_relpath``.

    Starts from committed static SVGs (works without basedata import), then overlays DB paths.
    When ``release_id`` is omitted, merge rows from all releases: for each ``T`` keep the path from
    the **highest** ``game_version`` that defines a non-empty lab sprite for that value.
    """

    out: dict[str, str] = dict(scan_committed_lab_sprite_identifier_map())

    if release_id is not None:
        release = resolve_lab_release_for_sprites(release_id=release_id)
        if release is None:
            return out
        qs = (
            ShapezGameIdentifier.objects.filter(release=release)
            .exclude(sprite_static_relpath="")
            .values_list("value", "sprite_static_relpath")
        )
        for value, relpath in qs.iterator(chunk_size=500):
            if value and relpath:
                out[str(value)] = str(relpath)
        return out

    rows = (
        ShapezGameIdentifier.objects.exclude(sprite_static_relpath="")
        .select_related("release")
        .values_list("release__game_version", "value", "sprite_static_relpath")
    )
    best: dict[str, tuple[int, str]] = {}
    for gv, value, relpath in rows.iterator(chunk_size=500):
        if not value or not relpath:
            continue
        gvi = int(gv)
        prev = best.get(str(value))
        if prev is None or gvi > prev[0]:
            best[str(value)] = (gvi, str(relpath))
    for value, (_gv, relpath) in best.items():
        out[value] = relpath
    return out
