"""Build solver masks from decoded island blueprint JSON (STEP1 reconstruction)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_patch_interior import (
    compute_patch_interior_cells,
)
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import (
    PlotStyle,
    classify_layout_type,
    is_extraction_style,
    mining_surface_from_layout,
)


@dataclass(frozen=True, slots=True)
class AsteroidReconstruction:
    """MVP occupancy gate (see documents/plans/plan_asteroid_extraction_solver_occupancy_gate)."""

    blueprint_occupied_cells: frozenset[tuple[int, int]]
    extraction_shell_cells: frozenset[tuple[int, int]]
    belt_cells: frozenset[tuple[int, int]]
    pipe_cells: frozenset[tuple[int, int]]
    legacy_transport_cells: frozenset[tuple[int, int]]
    interior_patch_cells: frozenset[tuple[int, int]]
    mineable_placement_cells: frozenset[tuple[int, int]]
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    transport_hard_block_cells: frozenset[tuple[int, int]] = frozenset()
    solver_pipe_network_cells: frozenset[tuple[int, int]] = frozenset()


def _iter_entry_dicts(entries: Any) -> Any:
    if not isinstance(entries, list):
        return
    for item in entries:
        if isinstance(item, dict):
            yield item


def gather_bp_entries_recursive(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect layout dicts from BP.Entries plus nested Container/Building Entries when present."""

    out: list[dict[str, Any]] = []
    bp = decoded.get("BP")
    stack: list[Any] = [bp if isinstance(bp, dict) else None]

    visited_ids: set[int] = set()
    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        nid = id(node)
        if nid in visited_ids:
            continue
        visited_ids.add(nid)

        raw = node.get("Entries")
        entries = raw if isinstance(raw, list) else []
        out.extend(entry for entry in _iter_entry_dicts(entries))
        nested = (
            ("Building", node.get("Building")),
            ("SubBuilding", node.get("SubBuilding")),
        )
        for _name, blob in nested:
            if isinstance(blob, dict):
                stack.append(blob)
    return out


def reconstruct_from_decoded(decoded: dict[str, Any]) -> AsteroidReconstruction | None:
    """Parse blueprint placements; returns ``None`` when no nonzero-grid entries exist."""

    blueprint_occupied_cells: set[tuple[int, int]] = set()
    extraction_shell_cells: set[tuple[int, int]] = set()
    belt_cells: set[tuple[int, int]] = set()
    pipe_cells: set[tuple[int, int]] = set()

    for item in gather_bp_entries_recursive(decoded):
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0

        xy = (x_val, y_val)
        t_raw = item.get("T")
        t_str: str | None
        if isinstance(t_raw, str):
            t_str = t_raw
        elif t_raw is None:
            t_str = None
        else:
            t_str = str(t_raw)

        style = classify_layout_type(t_str)
        blueprint_occupied_cells.add(xy)
        if style == PlotStyle.belt:
            belt_cells.add(xy)
        elif style == PlotStyle.pipe:
            pipe_cells.add(xy)
        if is_extraction_style(style):
            extraction_shell_cells.add(xy)

    if not blueprint_occupied_cells:
        return None

    xs = [c[0] for c in blueprint_occupied_cells]
    ys = [c[1] for c in blueprint_occupied_cells]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)

    interior_patch_list = compute_patch_interior_cells(extraction_shell_cells)
    interior_patch_cells = frozenset(interior_patch_list)

    legacy_transport_set = belt_cells | pipe_cells
    mineable = frozenset(
        c
        for c in (extraction_shell_cells | interior_patch_cells) - legacy_transport_set
        if c[0] != 0
    )

    return AsteroidReconstruction(
        blueprint_occupied_cells=frozenset(blueprint_occupied_cells),
        extraction_shell_cells=frozenset(extraction_shell_cells),
        belt_cells=frozenset(belt_cells),
        pipe_cells=frozenset(pipe_cells),
        legacy_transport_cells=frozenset(legacy_transport_set),
        interior_patch_cells=interior_patch_cells,
        mineable_placement_cells=frozenset(mineable),
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )


def asteroid_bbox_extended(
    rec: AsteroidReconstruction,
    *,
    exterior_margin: int,
) -> tuple[int, int, int, int]:
    """Tight XY bounds ± ``exterior_margin`` for routing canvases."""

    return (
        rec.x_min - exterior_margin,
        rec.x_max + exterior_margin,
        rec.y_min - exterior_margin,
        rec.y_max + exterior_margin,
    )


def is_exterior_coord(
    x: int,
    y: int,
    *,
    rec: AsteroidReconstruction,
    exterior_margin: int,
) -> bool:
    """``True`` when at least ``exterior_margin`` cells outside mined blueprint bbox."""

    return (
        x < rec.x_min - exterior_margin
        or x > rec.x_max + exterior_margin
        or y < rec.y_min - exterior_margin
        or y > rec.y_max + exterior_margin
    )


def dominant_surface_from_shell(decoded: dict[str, Any]) -> str:
    """Rough ``shape`` / ``fluid`` hint from extraction-shell layout names."""

    hints = mining_surfaces_from_shell(decoded)
    if "fluid" in hints:
        return "fluid"
    if "shape" in hints:
        return "shape"
    return "shape"


def mining_surfaces_from_shell(decoded: dict[str, Any]) -> frozenset[str]:
    """디코드된 채굴류 엔트리에서 필요한 surface 집합을 반환한다."""

    hints: set[str] = set()
    for item in gather_bp_entries_recursive(decoded):
        t_raw = item.get("T")
        t_str = t_raw if isinstance(t_raw, str) else str(t_raw) if t_raw is not None else None
        surface = mining_surface_from_layout(t_str)
        if surface is not None:
            hints.add(surface)
    return frozenset(hints)
