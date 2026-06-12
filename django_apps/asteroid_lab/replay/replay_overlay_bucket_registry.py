"""Typed registry for ``cell_overlay_json`` bucket harvest by consumer role."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Flag, auto

from django_apps.asteroid_lab.typing_boundary import JsonObject

SEMANTIC_LOOKUP = "semantic_lookup"
PAINT_TARGET = "paint_target"


class OverlayBucketRole(Flag):
    """Which replay consumers may read a persisted overlay bucket."""

    SEMANTIC_LOOKUP = auto()
    PAINT_TARGET = auto()


@dataclass(frozen=True, slots=True)
class OverlayBucketSpec:
    key: str
    roles: OverlayBucketRole
    harvest: Callable[[JsonObject, list[JsonObject]], None]


def _append_cells(out: list[JsonObject], lst: object) -> None:
    if not isinstance(lst, list):
        return
    for cell in lst:
        if isinstance(cell, dict):
            out.append(dict(cell))


def _push_from_blocks(out: list[JsonObject], blocks: object) -> None:
    if not isinstance(blocks, list):
        return
    for block in blocks:
        if not isinstance(block, dict):
            continue
        cells = block.get("cells")
        if isinstance(cells, list):
            _append_cells(out, cells)
        elif block.get("x") is not None and block.get("y") is not None:
            out.append(dict(block))


def _harvest_cell_list(key: str) -> Callable[[JsonObject, list[JsonObject]], None]:
    def _harvest(overlay: JsonObject, out: list[JsonObject]) -> None:
        _append_cells(out, overlay.get(key))

    return _harvest


def _harvest_cell_blocks(key: str) -> Callable[[JsonObject, list[JsonObject]], None]:
    def _harvest(overlay: JsonObject, out: list[JsonObject]) -> None:
        _push_from_blocks(out, overlay.get(key))

    return _harvest


def _harvest_blocks_cells_json(key: str) -> Callable[[JsonObject, list[JsonObject]], None]:
    def _harvest(overlay: JsonObject, out: list[JsonObject]) -> None:
        blocks = overlay.get(key)
        if not isinstance(blocks, list):
            return
        for block in blocks:
            if not isinstance(block, dict):
                continue
            _append_cells(out, block.get("cells_json"))

    return _harvest


def _harvest_main_component_candidate(overlay: JsonObject, out: list[JsonObject]) -> None:
    main = overlay.get("main_component_candidate")
    if not isinstance(main, dict):
        return
    cells_json = main.get("cells_json")
    if isinstance(cells_json, list):
        _append_cells(out, cells_json)
    elif main.get("x") is not None and main.get("y") is not None:
        out.append(dict(main))


def _harvest_dynamic_dict_cells_json(overlay: JsonObject, out: list[JsonObject]) -> None:
    handled = _registry_handled_keys()
    for key, val in overlay.items():
        if key in handled or not isinstance(val, dict) or isinstance(val, list):
            continue
        cells_json = val.get("cells_json")
        if isinstance(cells_json, list):
            _append_cells(out, cells_json)


_OVERLAY_BUCKET_REGISTRY: tuple[OverlayBucketSpec, ...] = (
    OverlayBucketSpec(
        "cells",
        OverlayBucketRole.SEMANTIC_LOOKUP | OverlayBucketRole.PAINT_TARGET,
        _harvest_cell_list("cells"),
    ),
    OverlayBucketSpec(
        "equipment_cells",
        OverlayBucketRole.SEMANTIC_LOOKUP | OverlayBucketRole.PAINT_TARGET,
        _harvest_cell_list("equipment_cells"),
    ),
    OverlayBucketSpec(
        "equipment",
        OverlayBucketRole.SEMANTIC_LOOKUP | OverlayBucketRole.PAINT_TARGET,
        _harvest_cell_list("equipment"),
    ),
    OverlayBucketSpec(
        "adjacent_transport",
        OverlayBucketRole.SEMANTIC_LOOKUP | OverlayBucketRole.PAINT_TARGET,
        _harvest_cell_list("adjacent_transport"),
    ),
    OverlayBucketSpec(
        "components",
        OverlayBucketRole.SEMANTIC_LOOKUP,
        _harvest_cell_blocks("components"),
    ),
    OverlayBucketSpec(
        "transport_components",
        OverlayBucketRole.SEMANTIC_LOOKUP,
        _harvest_cell_blocks("transport_components"),
    ),
    OverlayBucketSpec(
        "transport",
        OverlayBucketRole.SEMANTIC_LOOKUP | OverlayBucketRole.PAINT_TARGET,
        _harvest_cell_list("transport"),
    ),
    OverlayBucketSpec(
        "main_component_candidate",
        OverlayBucketRole.SEMANTIC_LOOKUP,
        _harvest_main_component_candidate,
    ),
    OverlayBucketSpec(
        "cleanup_candidate_cells",
        OverlayBucketRole.SEMANTIC_LOOKUP,
        _harvest_cell_list("cleanup_candidate_cells"),
    ),
    OverlayBucketSpec(
        "equipment_bundles",
        OverlayBucketRole.PAINT_TARGET,
        _harvest_blocks_cells_json("equipment_bundles"),
    ),
)


def _registry_handled_keys() -> frozenset[str]:
    return frozenset(spec.key for spec in _OVERLAY_BUCKET_REGISTRY)


def overlay_bucket_specs(*, role: OverlayBucketRole | None = None) -> tuple[OverlayBucketSpec, ...]:
    if role is None:
        return _OVERLAY_BUCKET_REGISTRY
    return tuple(spec for spec in _OVERLAY_BUCKET_REGISTRY if role in spec.roles)


def collect_overlay_cells_for_role(
    overlay: JsonObject,
    role: OverlayBucketRole,
) -> list[JsonObject]:
    """Harvest overlay cell rows for one registry role (stable bucket order)."""

    if not isinstance(overlay, dict):
        return []
    out: list[JsonObject] = []
    for spec in overlay_bucket_specs(role=role):
        spec.harvest(overlay, out)
    if role is OverlayBucketRole.SEMANTIC_LOOKUP:
        _harvest_dynamic_dict_cells_json(overlay, out)
    return out


def collect_overlay_cells_for_semantic_lookup(overlay: JsonObject) -> list[JsonObject]:
    return collect_overlay_cells_for_role(overlay, OverlayBucketRole.SEMANTIC_LOOKUP)


def collect_overlay_cells_for_paint_target(overlay: JsonObject) -> list[JsonObject]:
    return collect_overlay_cells_for_role(overlay, OverlayBucketRole.PAINT_TARGET)


def overlay_bucket_keys_for_role(role: OverlayBucketRole) -> tuple[str, ...]:
    return tuple(spec.key for spec in overlay_bucket_specs(role=role))


__all__ = [
    "PAINT_TARGET",
    "SEMANTIC_LOOKUP",
    "OverlayBucketRole",
    "OverlayBucketSpec",
    "collect_overlay_cells_for_paint_target",
    "collect_overlay_cells_for_role",
    "collect_overlay_cells_for_semantic_lookup",
    "overlay_bucket_keys_for_role",
    "overlay_bucket_specs",
]
