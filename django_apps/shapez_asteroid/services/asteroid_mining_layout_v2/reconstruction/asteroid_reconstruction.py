"""
STEP 1 — Asteroid reconstruction (CANON ``05_step1_reconstruction.md`` §6).

Blueprint scan → asteroid shell / transport / equipment / barriers → outside flood
(with Chebyshev closing on the **transport-stripped hull** ``full_barrier − belt − pipe``,
matching copy-preview strip semantics) → inferred **interior mining-region candidates**
(cells inside that closed perimeter with no blueprint row) → ``mineable_placement_cells``.

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
from dataclasses import dataclass, field
from typing import Any, Literal

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedExistingLayoutContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    AsteroidResourceKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    physical_column_count_inclusive,
    step_blueprint_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.reconstruction import (
    MineableCellSemantic,
    MineableSemanticSource,
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import (
    PlotStyle,
    classify_layout_type,
    mining_surface_from_layout,
)

from ..domain.decoded_blueprint import DecodedBlueprintDocument
from .patch_interior import compute_patch_interior_cells

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


def _four_neighbors(c: BlueprintCell) -> tuple[BlueprintCell, ...]:
    return tuple(step_blueprint_cell(c, d) for d in _CARDINAL)


def infer_asteroid_resource_kind_from_shell_layout_t(t_str: str | None) -> AsteroidResourceKind:
    """Shape vs fluid asteroid field from shell ``T`` (last blueprint row wins on overlay)."""

    if not t_str:
        return AsteroidResourceKind.UNKNOWN_ASTEROID
    c = str(t_str).strip().lower().replace("_", "")
    if "fluid" in c or "liquid" in c:
        return AsteroidResourceKind.FLUID_ASTEROID
    if "asteroidfield" in c:
        return AsteroidResourceKind.SHAPE_ASTEROID
    return AsteroidResourceKind.UNKNOWN_ASTEROID


def infer_asteroid_resource_kind_from_equipment_layout_t(t_str: str | None) -> AsteroidResourceKind:
    surf = mining_surface_from_layout(t_str)
    if surf == "fluid":
        return AsteroidResourceKind.FLUID_ASTEROID
    if surf == "shape":
        return AsteroidResourceKind.SHAPE_ASTEROID
    return AsteroidResourceKind.UNKNOWN_ASTEROID


def _merge_adjacent_resource_kinds(kinds: set[AsteroidResourceKind]) -> AsteroidResourceKind:
    """Collapse UNKNOWN; if both SHAPE and FLUID appear, UNKNOWN (no silent coercion)."""

    core = {k for k in kinds if k is not AsteroidResourceKind.UNKNOWN_ASTEROID}
    if len(core) > 1:
        return AsteroidResourceKind.UNKNOWN_ASTEROID
    if len(core) == 1:
        return next(iter(core))
    return AsteroidResourceKind.UNKNOWN_ASTEROID


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
        out.extend(_iter_entry_dicts(entries))
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


def validate_reconstruction_placement_contract(dto: ReconstructionDTO) -> None:
    """``interior_patch_cells ⊆ mineable_placement_cells`` (STEP 1 → Pass1 contract)."""

    interior_f = frozenset(dto.interior_patch_cells)
    mineable_f = frozenset(dto.mineable_placement_cells)
    if interior_f - mineable_f:
        extra = sorted(interior_f - mineable_f, key=lambda c: (c[1], c[0]))[:24]
        msg = f"interior_patch_cells must be subset of mineable_placement_cells; extra={extra!r}"
        raise ValueError(msg)


def validate_reconstruction_semantic_contract(dto: ReconstructionDTO) -> None:
    """Mineable coordinates ↔ semantics coverage; barriers must not carry mineable semantics."""

    validate_reconstruction_placement_contract(dto)
    mineable_f = frozenset(dto.mineable_placement_cells)
    sem_by_cell = {s.cell: s for s in dto.mineable_cell_semantics}
    if not mineable_f:
        if dto.mineable_cell_semantics:
            raise ValueError(
                "mineable_cell_semantics must be empty when mineable_placement_cells is empty"
            )
        return
    if set(sem_by_cell) != mineable_f:
        missing = sorted(mineable_f - set(sem_by_cell), key=lambda c: (c[1], c[0]))[:24]
        extra = sorted(set(sem_by_cell) - mineable_f, key=lambda c: (c[1], c[0]))[:24]
        msg = (
            "mineable_cell_semantics must cover exactly mineable_placement_cells; "
            f"missing={missing!r} extra={extra!r}"
        )
        raise ValueError(msg)
    permanent_block = frozenset(dto.belt_cells) | frozenset(dto.pipe_cells)
    for s in dto.mineable_cell_semantics:
        if s.cell in permanent_block:
            msg = f"mineable semantic on belt/pipe cell is forbidden: {s.cell!r}"
            raise ValueError(msg)


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


@dataclass
class _ReconstructBarrierBuckets:
    full_barrier_cells: set[BlueprintCell] = field(default_factory=set)
    asteroid_shell_cells: set[BlueprintCell] = field(default_factory=set)
    belt_cells: set[BlueprintCell] = field(default_factory=set)
    pipe_cells: set[BlueprintCell] = field(default_factory=set)
    extractor_cells: set[BlueprintCell] = field(default_factory=set)
    extension_cells: set[BlueprintCell] = field(default_factory=set)
    platform_cells: set[BlueprintCell] = field(default_factory=set)
    other_barrier_cells: set[BlueprintCell] = field(default_factory=set)
    shell_t_by_cell: dict[BlueprintCell, str | None] = field(default_factory=dict)
    equipment_t_by_cell: dict[BlueprintCell, str | None] = field(default_factory=dict)


def _reconstruct_mutable_doc(
    decoded_blueprint: dict[str, Any] | DecodedBlueprintDocument,
) -> dict[str, Any]:
    return (
        decoded_blueprint.as_mutable_dict()
        if isinstance(decoded_blueprint, DecodedBlueprintDocument)
        else dict(decoded_blueprint)
    )


def _reconstruct_entry_t_str(t_raw: Any) -> str | None:
    if isinstance(t_raw, str):
        return t_raw
    if t_raw is None:
        return None
    return str(t_raw)


def _reconstruct_entry_xy_or_skip(item: dict[str, Any]) -> BlueprintCell | None:
    x_val = _int_or_none(item.get("X"))
    # Shapez blueprint: X==0 is not ingested as a cell id (CANON STEP1 §6.2.1). That is
    # a label skip, not a physical void column between neighbors.
    if x_val is None or x_val == 0:
        return None
    y_val = _int_or_none(item.get("Y"))
    if y_val is None:
        y_val = 0
    return (x_val, y_val)


def _reconstruct_classify_cell_into_buckets(
    xy: BlueprintCell,
    t_str: str | None,
    b: _ReconstructBarrierBuckets,
) -> None:
    b.full_barrier_cells.add(xy)
    if _is_asteroid_shell_layout_type(t_str):
        b.asteroid_shell_cells.add(xy)
        b.shell_t_by_cell[xy] = t_str
        return

    style = classify_layout_type(t_str)
    if style is PlotStyle.belt:
        b.belt_cells.add(xy)
    elif style is PlotStyle.pipe:
        b.pipe_cells.add(xy)
    elif style in (
        PlotStyle.fluid_miner,
        PlotStyle.miner,
        PlotStyle.extractor,
        PlotStyle.booster,
    ):
        b.extractor_cells.add(xy)
        b.equipment_t_by_cell[xy] = t_str
    elif style in (PlotStyle.extension, PlotStyle.fluid_extension):
        b.extension_cells.add(xy)
        b.equipment_t_by_cell[xy] = t_str
    elif style is PlotStyle.platform:
        b.platform_cells.add(xy)
    else:
        b.other_barrier_cells.add(xy)


def _reconstruct_collect_barrier_buckets(doc: dict[str, Any]) -> _ReconstructBarrierBuckets:
    b = _ReconstructBarrierBuckets()
    for item in gather_bp_entries_recursive(doc):
        xy = _reconstruct_entry_xy_or_skip(item)
        if xy is None:
            continue
        t_str = _reconstruct_entry_t_str(item.get("T"))
        _reconstruct_classify_cell_into_buckets(xy, t_str, b)
    return b


def _reconstruct_interior_patch(
    full_barrier_cells: set[BlueprintCell],
    belt_cells: set[BlueprintCell],
    pipe_cells: set[BlueprintCell],
) -> tuple[set[BlueprintCell], tuple[BlueprintCell, ...]]:
    hull_for_interior_inference = full_barrier_cells - belt_cells - pipe_cells
    interior_raw = compute_patch_interior_cells(
        set(hull_for_interior_inference),
        perimeter_bridge_steps=1,
    )
    interior_set = {c for c in interior_raw if c not in full_barrier_cells}
    return interior_set, _sorted_cells(interior_set)


def _reconstruct_mineable_cells(
    b: _ReconstructBarrierBuckets,
    interior_set: set[BlueprintCell],
) -> set[BlueprintCell]:
    equipment_footprint = b.extractor_cells | b.extension_cells
    permanent_blocking_for_mineable = (
        b.belt_cells | b.pipe_cells | b.platform_cells | b.other_barrier_cells
    )
    mineable_base = b.asteroid_shell_cells | interior_set | equipment_footprint
    mineable: set[BlueprintCell] = set()
    for c in mineable_base:
        if not is_physical_x(c[0]):
            continue
        if c in permanent_blocking_for_mineable:
            continue
        mineable.add(c)
    return mineable


def _shell_kind_by_cell(b: _ReconstructBarrierBuckets) -> dict[BlueprintCell, AsteroidResourceKind]:
    return {
        xy: infer_asteroid_resource_kind_from_shell_layout_t(b.shell_t_by_cell.get(xy))
        for xy in b.asteroid_shell_cells
    }


def _interior_inferred_kind_by_cell(
    interior_set: set[BlueprintCell],
    shell_cells: set[BlueprintCell],
    shell_kind: dict[BlueprintCell, AsteroidResourceKind],
    equipment_cells: set[BlueprintCell],
    equipment_t: dict[BlueprintCell, str | None],
) -> dict[BlueprintCell, AsteroidResourceKind]:
    if not interior_set:
        return {}
    out: dict[BlueprintCell, AsteroidResourceKind] = {}
    remaining = set(interior_set)
    while remaining:
        seed = min(remaining, key=lambda c: (c[1], c[0]))
        stack: list[BlueprintCell] = [seed]
        comp: set[BlueprintCell] = set()
        while stack:
            c = stack.pop()
            if c not in remaining:
                continue
            remaining.remove(c)
            comp.add(c)
            for n in _four_neighbors(c):
                if n in remaining:
                    stack.append(n)
        shell_touch: set[AsteroidResourceKind] = set()
        eq_touch: set[AsteroidResourceKind] = set()
        for c in comp:
            for n in _four_neighbors(c):
                if n in shell_cells:
                    shell_touch.add(shell_kind.get(n, AsteroidResourceKind.UNKNOWN_ASTEROID))
                if n in equipment_cells:
                    eq_touch.add(
                        infer_asteroid_resource_kind_from_equipment_layout_t(equipment_t.get(n))
                    )
        merged_shell = _merge_adjacent_resource_kinds(shell_touch)
        kind: AsteroidResourceKind
        if merged_shell is not AsteroidResourceKind.UNKNOWN_ASTEROID:
            kind = merged_shell
        else:
            kind = _merge_adjacent_resource_kinds(eq_touch)
        for c in comp:
            out[c] = kind
    return out


def _equipment_only_semantic_kind(
    xy: BlueprintCell,
    shell_cells: set[BlueprintCell],
    shell_kind: dict[BlueprintCell, AsteroidResourceKind],
    equipment_t: dict[BlueprintCell, str | None],
) -> AsteroidResourceKind:
    adj_shell: set[AsteroidResourceKind] = set()
    for n in _four_neighbors(xy):
        if n in shell_cells:
            adj_shell.add(shell_kind.get(n, AsteroidResourceKind.UNKNOWN_ASTEROID))
    merged = _merge_adjacent_resource_kinds(adj_shell)
    if merged is not AsteroidResourceKind.UNKNOWN_ASTEROID:
        return merged
    return infer_asteroid_resource_kind_from_equipment_layout_t(equipment_t.get(xy))


def _build_mineable_cell_semantics(
    mineable: set[BlueprintCell],
    interior_set: set[BlueprintCell],
    b: _ReconstructBarrierBuckets,
    shell_kind: dict[BlueprintCell, AsteroidResourceKind],
    interior_kind: dict[BlueprintCell, AsteroidResourceKind],
    equipment_t: dict[BlueprintCell, str | None],
) -> tuple[MineableCellSemantic, ...]:
    shell_cells = b.asteroid_shell_cells
    out: list[MineableCellSemantic] = []
    for cell in _sorted_cells(mineable):
        src: MineableSemanticSource
        if cell in interior_set:
            rk = interior_kind[cell]
            src = "interior_patch_inferred"
        elif cell in shell_cells:
            rk = shell_kind[cell]
            src = "extraction_shell"
        else:
            rk = _equipment_only_semantic_kind(cell, shell_cells, shell_kind, equipment_t)
            src = "equipment_footprint"
        out.append(MineableCellSemantic(cell=cell, resource_kind=rk, source=src))
    return tuple(out)


def _reconstruct_external_bbox_margin(
    mineable_f: frozenset[BlueprintCell],
    shell_f: frozenset[BlueprintCell],
) -> tuple[BBox | None, Literal["mineable", "shell", "none"], int]:
    abox = _bbox_from_cells(mineable_f)
    margin_source: Literal["mineable", "shell", "none"] = "none"
    margin = 0
    if abox is not None:
        margin_source = "mineable"
        margin = _external_margin_from_bbox(abox)
        return abox, margin_source, margin

    sbox = _bbox_from_cells(shell_f)
    if sbox is None:
        return None, margin_source, margin

    margin = _external_margin_from_bbox(sbox)
    return sbox, "shell", margin


def _reconstruct_assert_physical_invariants(
    mineable: set[BlueprintCell],
    b: _ReconstructBarrierBuckets,
    equipment_footprint: set[BlueprintCell],
    interior_set: set[BlueprintCell],
) -> None:
    checks: list[tuple[str, Iterable[BlueprintCell]]] = [
        ("mineable_placement_cells", mineable),
        ("extraction_shell_cells", b.asteroid_shell_cells),
        ("full_barrier_cells", b.full_barrier_cells),
        ("belt_cells", b.belt_cells),
        ("pipe_cells", b.pipe_cells),
        ("extractor_cells", b.extractor_cells),
        ("extension_cells", b.extension_cells),
        ("equipment_footprint_mineable_cells", equipment_footprint),
        ("interior_patch_cells", interior_set),
    ]
    for label, cells in checks:
        _assert_physical_x_cells(label, cells)


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

    doc = _reconstruct_mutable_doc(decoded_blueprint)
    b = _reconstruct_collect_barrier_buckets(doc)

    if not b.full_barrier_cells:
        return ReconstructionDTO()

    # Match ``preview_reconstruction_timeline`` strip-transport hull: belt/pipe rows are
    # dropped before interior inference so corridors do not count as perimeter blockers.
    interior_set, interior_patch_cells = _reconstruct_interior_patch(
        b.full_barrier_cells,
        b.belt_cells,
        b.pipe_cells,
    )

    mineable = _reconstruct_mineable_cells(b, interior_set)
    equipment_footprint = b.extractor_cells | b.extension_cells

    shell_kind = _shell_kind_by_cell(b)
    equipment_cells = b.extractor_cells | b.extension_cells
    interior_kind = _interior_inferred_kind_by_cell(
        interior_set,
        b.asteroid_shell_cells,
        shell_kind,
        equipment_cells,
        b.equipment_t_by_cell,
    )
    mineable_semantics = _build_mineable_cell_semantics(
        mineable,
        interior_set,
        b,
        shell_kind,
        interior_kind,
        b.equipment_t_by_cell,
    )

    mineable_f = frozenset(mineable)
    shell_f = frozenset(b.asteroid_shell_cells)
    abox, margin_source, margin = _reconstruct_external_bbox_margin(mineable_f, shell_f)

    _reconstruct_assert_physical_invariants(mineable, b, equipment_footprint, interior_set)

    dto = ReconstructionDTO(
        mineable_placement_cells=_sorted_cells(mineable),
        extraction_shell_cells=_sorted_cells(b.asteroid_shell_cells),
        full_barrier_cells=_sorted_cells(b.full_barrier_cells),
        belt_cells=_sorted_cells(b.belt_cells),
        pipe_cells=_sorted_cells(b.pipe_cells),
        extractor_cells=_sorted_cells(b.extractor_cells),
        extension_cells=_sorted_cells(b.extension_cells),
        equipment_footprint_mineable_cells=_sorted_cells(equipment_footprint),
        interior_patch_cells=interior_patch_cells,
        mineable_cell_semantics=mineable_semantics,
        asteroid_bbox=abox,
        external_margin=margin,
        external_margin_bbox_source=margin_source,
    )
    validate_reconstruction_semantic_contract(dto)
    return dto


__all__ = [
    "gather_bp_entries_recursive",
    "infer_asteroid_resource_kind_from_equipment_layout_t",
    "infer_asteroid_resource_kind_from_shell_layout_t",
    "reconstruct_asteroid_mining_field",
    "validate_reconstruction_placement_contract",
    "validate_reconstruction_semantic_contract",
]
