"""
STEP 1 — Asteroid reconstruction (CANON ``05_step1_reconstruction.md`` §6).

Blueprint scan → asteroid shell / transport / equipment / barriers → outside flood
(with Chebyshev closing on the shell perimeter) → inferred **interior mining-region
candidates** (cells inside the closed shell perimeter with no blueprint row) →
``mineable_placement_cells``.

**Void wording (domain):** ``interior_set`` / ``interior_patch_cells`` are *not*
arbitrary map void or “air off the asteroid”. They are empty lattice sites inferred
to lie inside the restored asteroid patch after perimeter closing — i.e. valid
mining-region interior alongside ``asteroid_shell_cells`` and existing equipment
footprints. True **external** void (coordinates never occupied by this blueprint’s
mining-relevant rows) never enters ``mineable_placement_cells`` because only scanned
barrier coordinates seed the hull and footprints.

``mineable_placement_cells`` = shell ∪ inferred interior patch ∪ extractor ∪
extension footprints, minus **permanent** belt / pipe / platform / other solid
barriers (existing miners/extensions are not permanent blockers).

``DecodedExistingLayoutContext`` is accepted for API symmetry with STEP 0.5; it must
not define or replace mineable cells (§6.4). No v1 solver imports; no NDJSON/log input.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any, Literal

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedBlueprintDocument,
    DecodedExistingLayoutContext,
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    physical_column_count_inclusive,
)
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import PlotStyle, classify_layout_type

from .patch_interior import compute_patch_interior_cells


def _iter_entry_dicts(entries: Any) -> Any:
    if not isinstance(entries, list):
        return
    for item in entries:
        if isinstance(item, dict):
            yield item


def gather_bp_entries_recursive(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect layout dicts from BP.Entries plus nested Container/Building Entries."""

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


def _is_asteroid_shell_layout_type(layout_t: str | None) -> bool:
    """True for decoded ``T`` values that denote asteroid field / shell terrain."""

    if not layout_t:
        return False
    compact = str(layout_t).strip().lower().replace("_", "")
    return "asteroidfield" in compact


def _sorted_cells(cells: Iterable[BlueprintCell]) -> tuple[BlueprintCell, ...]:
    return tuple(sorted(cells, key=lambda c: (c[1], c[0])))


def _bbox_from_cells(cells: Iterable[BlueprintCell]) -> BBox | None:
    xs: list[int] = []
    ys: list[int] = []
    for x, y in cells:
        xs.append(x)
        ys.append(y)
    if not xs:
        return None
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _external_margin_from_bbox(b: BBox) -> int:
    """Dynamic margin (``01_project_overview.md`` §3.5)."""

    w = physical_column_count_inclusive(b.min_x, b.max_x)
    h = b.max_y - b.min_y + 1
    return max(3, min(7, int(math.ceil(max(w, h) * 0.15))))


def _assert_physical_x_cells(label: str, cells: Iterable[BlueprintCell]) -> None:
    bad = [c for c in cells if not is_physical_x(c[0])]
    if bad:
        msg = f"{label}: illegal x==0 cells {bad[:5]!r}"
        raise ValueError(msg)


def reconstruct_asteroid_mining_field(
    decoded_blueprint: dict[str, Any] | DecodedBlueprintDocument,
    decoded_existing_layout: DecodedExistingLayoutContext | None = None,
) -> ReconstructionDTO:
    """Populate ``ReconstructionDTO`` from decoded blueprint JSON (STEP 1).

    ``decoded_existing_layout`` is read-only solver context (STEP 0.5). It must not
    supply or override ``mineable_placement_cells``, ``extraction_shell_cells``, or
    interior inference (CANON §6.4).
    """

    _ = decoded_existing_layout

    doc = (
        decoded_blueprint.as_mutable_dict()
        if isinstance(decoded_blueprint, DecodedBlueprintDocument)
        else dict(decoded_blueprint)
    )

    full_barrier_cells: set[BlueprintCell] = set()
    asteroid_shell_cells: set[BlueprintCell] = set()
    belt_cells: set[BlueprintCell] = set()
    pipe_cells: set[BlueprintCell] = set()
    extractor_cells: set[BlueprintCell] = set()
    extension_cells: set[BlueprintCell] = set()
    platform_cells: set[BlueprintCell] = set()
    other_barrier_cells: set[BlueprintCell] = set()

    for item in gather_bp_entries_recursive(doc):
        x_val = _int_or_none(item.get("X"))
        # Shapez blueprint: X==0 is not ingested as a cell id (CANON STEP1 §6.2.1). That is
        # a label skip, not a physical void column between neighbors.
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0

        xy: BlueprintCell = (x_val, y_val)
        t_raw = item.get("T")
        if isinstance(t_raw, str):
            t_str: str | None = t_raw
        elif t_raw is None:
            t_str = None
        else:
            t_str = str(t_raw)

        full_barrier_cells.add(xy)

        if _is_asteroid_shell_layout_type(t_str):
            asteroid_shell_cells.add(xy)
            continue

        style = classify_layout_type(t_str)
        if style is PlotStyle.belt:
            belt_cells.add(xy)
        elif style is PlotStyle.pipe:
            pipe_cells.add(xy)
        elif style in (
            PlotStyle.fluid_miner,
            PlotStyle.miner,
            PlotStyle.extractor,
            PlotStyle.booster,
        ):
            extractor_cells.add(xy)
        elif style in (PlotStyle.extension, PlotStyle.fluid_extension):
            extension_cells.add(xy)
        elif style is PlotStyle.platform:
            platform_cells.add(xy)
        else:
            other_barrier_cells.add(xy)

    if not full_barrier_cells:
        return ReconstructionDTO()

    interior_raw = compute_patch_interior_cells(
        set(asteroid_shell_cells),
        perimeter_bridge_steps=1,
    )
    interior_set = {c for c in interior_raw if c not in full_barrier_cells}
    interior_patch_cells = _sorted_cells(interior_set)

    equipment_footprint = extractor_cells | extension_cells
    permanent_blocking_for_mineable = belt_cells | pipe_cells | platform_cells | other_barrier_cells
    mineable_base = asteroid_shell_cells | interior_set | equipment_footprint
    mineable: set[BlueprintCell] = set()
    for c in mineable_base:
        if not is_physical_x(c[0]):
            continue
        if c in permanent_blocking_for_mineable:
            continue
        mineable.add(c)

    mineable_f = frozenset(mineable)
    shell_f = frozenset(asteroid_shell_cells)

    abox = _bbox_from_cells(mineable_f)
    margin_source: Literal["mineable", "shell", "none"] = "none"
    margin = 0
    if abox is not None:
        margin_source = "mineable"
        margin = _external_margin_from_bbox(abox)
    else:
        sbox = _bbox_from_cells(shell_f)
        if sbox is not None:
            abox = sbox
            margin_source = "shell"
            margin = _external_margin_from_bbox(abox)

    _assert_physical_x_cells("mineable_placement_cells", mineable)
    _assert_physical_x_cells("extraction_shell_cells", asteroid_shell_cells)
    _assert_physical_x_cells("full_barrier_cells", full_barrier_cells)
    _assert_physical_x_cells("belt_cells", belt_cells)
    _assert_physical_x_cells("pipe_cells", pipe_cells)
    _assert_physical_x_cells("extractor_cells", extractor_cells)
    _assert_physical_x_cells("extension_cells", extension_cells)
    _assert_physical_x_cells("equipment_footprint_mineable_cells", equipment_footprint)
    _assert_physical_x_cells("interior_patch_cells", interior_set)

    return ReconstructionDTO(
        mineable_placement_cells=_sorted_cells(mineable),
        extraction_shell_cells=_sorted_cells(asteroid_shell_cells),
        full_barrier_cells=_sorted_cells(full_barrier_cells),
        belt_cells=_sorted_cells(belt_cells),
        pipe_cells=_sorted_cells(pipe_cells),
        extractor_cells=_sorted_cells(extractor_cells),
        extension_cells=_sorted_cells(extension_cells),
        equipment_footprint_mineable_cells=_sorted_cells(equipment_footprint),
        interior_patch_cells=interior_patch_cells,
        asteroid_bbox=abox,
        external_margin=margin,
        external_margin_bbox_source=margin_source,
    )


__all__ = [
    "gather_bp_entries_recursive",
    "reconstruct_asteroid_mining_field",
]
