"""
STEP 0.5 — Existing layout analysis (``03_data_schema_dto.md`` §E, ``04_step0_decode`` §5.4).

Read-only solver context from decoded island JSON **before** STEP 1 reconstruction.
DTO shapes match §E; belt and pipe are analyzed as **separate** ``TransportKind`` graphs
(never merged into a mixed trunk).

Contracts (implementation must preserve):

1. ``ExistingLayoutAnalysis`` is read-only context (no blueprint mutation).
2. It does not modify placement algorithms or outputs.
3. It does **not** emit ``mineable_placement_cells`` (STEP 1 ``ReconstructionDTO`` only).
4. It does **not** replace or shadow reconstruction inputs.
5. ``TransportComponentStatus.MAIN_TRUNK_CANDIDATE`` cells feed ``trunk_seed_cell_union``.
6. ``ORPHAN_COMPONENT`` and ``SINGLE_CELL_ARTIFACT`` feed ``cleanup_candidate_cell_union``.
7. Hints are **not** ``hard_protected_corridors`` (protection is a downstream routing policy).
8. Each ``ExistingTransportAnalysis`` row is single-kind (belt **or** pipe).
9. Components are 4-neighbor CC within one kind only (§E.12).

``classify_layout_type`` maps blueprint ``T`` strings to belt/pipe/equipment; it lives in
``shapez_asteroid.services.style_classifier`` (layout labels only, not v1 solver).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox, Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    DecodedExistingLayoutContext,
    EquipmentTransportAttachment,
    ExistingEquipmentAnalysis,
    ExistingLayoutAnalysis,
    ExistingLayoutIssue,
    ExistingLayoutSolverHints,
    ExistingTransportAnalysis,
    TransportComponentSummary,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    EquipmentKind,
    ExistingLayoutIssueCode,
    ExistingLayoutIssueSeverity,
    SourceKind,
    TransportComponentStatus,
    TransportKind,
)
from django_apps.shapez_asteroid.services.style_classifier import PlotStyle, classify_layout_type

from ..domain.decoded_blueprint import DecodedBlueprintDocument

_CARDINAL: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def compute_transport_components(
    cells: frozenset[Coord],
    transport_kind: TransportKind,
) -> tuple[frozenset[Coord], ...]:
    """Same-kind 4-neighbor connected components (§E.12), deterministic ordering."""

    if not cells:
        return ()
    remaining: set[Coord] = set(cells)
    raw: list[frozenset[Coord]] = []
    while remaining:
        start = min(remaining, key=lambda c: (c.x, c.y))
        stack = [start]
        acc: set[Coord] = set()
        while stack:
            cur = stack.pop()
            if cur not in remaining:
                continue
            remaining.remove(cur)
            acc.add(cur)
            for dx, dy in _CARDINAL:
                nxt = Coord(cur.x + dx, cur.y + dy)
                if nxt in remaining:
                    stack.append(nxt)
        raw.append(frozenset(acc))
    raw.sort(key=lambda fs: (-len(fs), min((c.x, c.y) for c in fs)))
    _ = transport_kind
    return tuple(raw)


def analyze_decoded_layout(
    decoded_blueprint: dict[str, Any] | DecodedBlueprintDocument,
) -> ExistingLayoutAnalysis:
    """Build ``ExistingLayoutAnalysis`` from decoded island JSON (STEP 0.5)."""

    doc = (
        decoded_blueprint.as_mutable_dict()
        if isinstance(decoded_blueprint, DecodedBlueprintDocument)
        else dict(decoded_blueprint)
    )
    entries = _list_entries(doc)
    island_bbox = _entries_bbox(entries)
    belt_cells, pipe_cells, equipment_rows = _scan_entries(entries)

    belt_analysis, belt_coord_to_id = _analyze_transport_layer(
        TransportKind.SHAPE_BELT, belt_cells, island_bbox
    )
    pipe_analysis, pipe_coord_to_id = _analyze_transport_layer(
        TransportKind.FLUID_PIPE, pipe_cells, island_bbox
    )

    equipment = _analyze_equipment(
        equipment_rows,
        belt_cells,
        pipe_cells,
        belt_analysis,
        pipe_analysis,
        belt_coord_to_id,
        pipe_coord_to_id,
    )

    source_kind, ambiguous = _classify_source_kind(
        belt_cells=belt_cells,
        pipe_cells=pipe_cells,
        equipment_rows=equipment_rows,
    )

    issues = _collect_issues(
        belt_analysis=belt_analysis,
        pipe_analysis=pipe_analysis,
        equipment=equipment,
        source_ambiguous=ambiguous,
    )

    hints = _build_solver_hints(belt_analysis=belt_analysis, pipe_analysis=pipe_analysis)

    return ExistingLayoutAnalysis(
        source_kind=source_kind,
        island_bbox=island_bbox,
        belt_transport=belt_analysis,
        pipe_transport=pipe_analysis,
        equipment=equipment,
        issues=tuple(issues),
        solver_hints=hints,
    )


def analyze_to_context(
    decoded_blueprint: dict[str, Any] | DecodedBlueprintDocument,
) -> DecodedExistingLayoutContext:
    """Convenience: wrap ``ExistingLayoutAnalysis`` in ``DecodedExistingLayoutContext``."""

    return DecodedExistingLayoutContext(analysis=analyze_decoded_layout(decoded_blueprint))


def trivial_unknown_analysis() -> ExistingLayoutAnalysis:
    """Minimal placeholder for callers that need a syntactically valid empty analysis."""

    empty_belt = _empty_transport(TransportKind.SHAPE_BELT)
    empty_pipe = _empty_transport(TransportKind.FLUID_PIPE)
    empty_eq = ExistingEquipmentAnalysis(
        miner_count=0,
        extension_count=0,
        miners_without_adjacent_transport=(),
        miners_attached_to_orphan_transport=(),
        equipment_attachment=(),
    )
    hints = ExistingLayoutSolverHints(
        trunk_seed_cell_union=frozenset(),
        cleanup_candidate_cell_union=frozenset(),
    )
    return ExistingLayoutAnalysis(
        source_kind=SourceKind.UNKNOWN,
        island_bbox=BBox(min_x=1, min_y=1, max_x=1, max_y=1),
        belt_transport=empty_belt,
        pipe_transport=empty_pipe,
        equipment=empty_eq,
        issues=(),
        solver_hints=hints,
    )


def _empty_transport(kind: TransportKind) -> ExistingTransportAnalysis:
    return ExistingTransportAnalysis(
        transport_kind=kind,
        component_count=0,
        main_component_id=None,
        components=(),
        orphan_component_ids=(),
        single_cell_artifacts=(),
    )


def _list_entries(decoded: dict[str, Any]) -> list[dict[str, Any]]:
    bp = decoded.get("BP")
    if not isinstance(bp, Mapping):
        return []
    raw = bp.get("Entries")
    if not isinstance(raw, list):
        return []
    return [e for e in raw if isinstance(e, dict)]


def _int_coord(entry: dict[str, Any]) -> Coord | None:
    try:
        xv = entry["X"]
        yv = entry["Y"]
    except KeyError:
        return None
    if isinstance(xv, bool) or isinstance(yv, bool):
        return None
    try:
        x = int(xv)
        y = int(yv)
    except (TypeError, ValueError):
        return None
    if x == 0:
        return None
    return Coord(x=x, y=y)


def _entries_bbox(entries: Iterable[dict[str, Any]]) -> BBox:
    coords = [c for e in entries if (c := _int_coord(e)) is not None]
    if not coords:
        return BBox(min_x=1, min_y=1, max_x=1, max_y=1)
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _on_island_margin(c: Coord, bbox: BBox) -> bool:
    return c.x in (bbox.min_x, bbox.max_x) or c.y in (bbox.min_y, bbox.max_y)


def _bbox_for_cells(cells: Iterable[Coord]) -> BBox:
    cl = list(cells)
    if not cl:
        return BBox(min_x=1, min_y=1, max_x=1, max_y=1)
    xs = [c.x for c in cl]
    ys = [c.y for c in cl]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _scan_entries(
    entries: list[dict[str, Any]],
) -> tuple[frozenset[Coord], frozenset[Coord], list[tuple[Coord, EquipmentKind, str | None]]]:
    belt: set[Coord] = set()
    pipe: set[Coord] = set()
    equipment: list[tuple[Coord, EquipmentKind, str | None]] = []
    for e in entries:
        c = _int_coord(e)
        if c is None:
            continue
        t = e.get("T")
        layout_t = str(t) if t is not None else ""
        style = classify_layout_type(layout_t)
        if style is PlotStyle.belt:
            belt.add(c)
            continue
        if style is PlotStyle.pipe:
            pipe.add(c)
            continue
        if style is PlotStyle.fluid_miner:
            equipment.append((c, EquipmentKind.FLUID_MINER, layout_t))
            continue
        if style is PlotStyle.miner:
            equipment.append((c, EquipmentKind.SHAPE_MINER, layout_t))
            continue
        if style in (PlotStyle.extension, PlotStyle.fluid_extension):
            equipment.append((c, EquipmentKind.EXTENSION, layout_t))
            continue
    return frozenset(belt), frozenset(pipe), equipment


def _analyze_transport_layer(
    kind: TransportKind,
    cells: frozenset[Coord],
    island_bbox: BBox,
) -> tuple[ExistingTransportAnalysis, dict[Coord, int]]:
    comps = list(compute_transport_components(cells, kind))
    multi = [c for c in comps if len(c) > 1]
    single = [c for c in comps if len(c) == 1]
    multi.sort(key=lambda fs: (-len(fs), min((c.x, c.y) for c in fs)))
    single.sort(key=lambda fs: min((c.x, c.y) for c in fs))
    ordered = multi + single
    main_comp: frozenset[Coord] | None = multi[0] if multi else None

    summaries: list[TransportComponentSummary] = []
    coord_to_id: dict[Coord, int] = {}
    orphan_ids: list[int] = []
    single_cells: list[Coord] = []

    for cid, comp in enumerate(ordered):
        for cell in comp:
            coord_to_id[cell] = cid
        bbox = _bbox_for_cells(comp)
        touches_margin = any(_on_island_margin(c, island_bbox) for c in comp)
        if len(comp) == 1:
            status = TransportComponentStatus.SINGLE_CELL_ARTIFACT
            single_cells.append(next(iter(comp)))
        elif main_comp is not None and comp == main_comp:
            status = TransportComponentStatus.MAIN_TRUNK_CANDIDATE
        else:
            status = TransportComponentStatus.ORPHAN_COMPONENT
            orphan_ids.append(cid)

        summaries.append(
            TransportComponentSummary(
                component_id=cid,
                kind=kind,
                cells=comp,
                cell_count=len(comp),
                bbox=bbox,
                touches_external_margin=touches_margin,
                status=status,
            )
        )

    main_id = 0 if main_comp is not None else None

    analysis = ExistingTransportAnalysis(
        transport_kind=kind,
        component_count=len(ordered),
        main_component_id=main_id,
        components=tuple(summaries),
        orphan_component_ids=tuple(orphan_ids),
        single_cell_artifacts=tuple(sorted(single_cells, key=lambda c: (c.x, c.y))),
    )
    return analysis, coord_to_id


def _extension_surface(layout_t: str | None) -> str | None:
    if layout_t is None:
        return None
    low = layout_t.lower()
    if "fluid" in low:
        return "fluid"
    return "shape"


def _component_status(
    analysis: ExistingTransportAnalysis, comp_id: int
) -> TransportComponentStatus:
    return next(s.status for s in analysis.components if s.component_id == comp_id)


def _analyze_equipment(
    equipment_rows: list[tuple[Coord, EquipmentKind, str | None]],
    belt_cells: frozenset[Coord],
    pipe_cells: frozenset[Coord],
    belt_analysis: ExistingTransportAnalysis,
    pipe_analysis: ExistingTransportAnalysis,
    belt_map: dict[Coord, int],
    pipe_map: dict[Coord, int],
) -> ExistingEquipmentAnalysis:
    attachments: list[EquipmentTransportAttachment] = []
    no_transport: list[Coord] = []
    orphan_attached: list[Coord] = []
    miner_count = 0
    ext_count = 0

    for coord, ek, layout_t in sorted(equipment_rows, key=lambda r: (r[0].x, r[0].y)):
        if ek in (EquipmentKind.SHAPE_MINER, EquipmentKind.FLUID_MINER):
            miner_count += 1
        elif ek is EquipmentKind.EXTENSION:
            ext_count += 1

        want_belt = ek is EquipmentKind.SHAPE_MINER or (
            ek is EquipmentKind.EXTENSION and _extension_surface(layout_t) == "shape"
        )
        want_pipe = ek is EquipmentKind.FLUID_MINER or (
            ek is EquipmentKind.EXTENSION and _extension_surface(layout_t) == "fluid"
        )

        adj_coords: list[Coord] = []
        comp_ids: list[int] = []
        touches_main = False

        for dx, dy in _CARDINAL:
            n = Coord(coord.x + dx, coord.y + dy)
            if want_belt and n in belt_cells:
                adj_coords.append(n)
                bid = belt_map[n]
                comp_ids.append(bid)
                if (
                    _component_status(belt_analysis, bid)
                    is TransportComponentStatus.MAIN_TRUNK_CANDIDATE
                ):
                    touches_main = True
            if want_pipe and n in pipe_cells:
                adj_coords.append(n)
                pid = pipe_map[n]
                comp_ids.append(pid)
                if (
                    _component_status(pipe_analysis, pid)
                    is TransportComponentStatus.MAIN_TRUNK_CANDIDATE
                ):
                    touches_main = True

        adj_sorted = tuple(sorted(set(adj_coords), key=lambda c: (c.x, c.y)))
        comp_ids_sorted = tuple(sorted(set(comp_ids)))

        if ek in (EquipmentKind.SHAPE_MINER, EquipmentKind.FLUID_MINER):
            if not adj_sorted:
                no_transport.append(coord)
            elif not touches_main:
                orphan_attached.append(coord)

        attachments.append(
            EquipmentTransportAttachment(
                equipment_coord=coord,
                equipment_kind=ek,
                adjacent_transport_coords=adj_sorted,
                adjacent_component_ids=comp_ids_sorted,
                attached_to_main_component=touches_main,
            )
        )

    return ExistingEquipmentAnalysis(
        miner_count=miner_count,
        extension_count=ext_count,
        miners_without_adjacent_transport=tuple(sorted(no_transport, key=lambda c: (c.x, c.y))),
        miners_attached_to_orphan_transport=tuple(
            sorted(orphan_attached, key=lambda c: (c.x, c.y))
        ),
        equipment_attachment=tuple(attachments),
    )


def _classify_source_kind(
    *,
    belt_cells: frozenset[Coord],
    pipe_cells: frozenset[Coord],
    equipment_rows: list[tuple[Coord, EquipmentKind, str | None]],
) -> tuple[SourceKind, bool]:
    has_belt = bool(belt_cells)
    has_pipe = bool(pipe_cells)
    has_shape_miner = any(ek is EquipmentKind.SHAPE_MINER for _, ek, _ in equipment_rows)
    has_fluid_miner = any(ek is EquipmentKind.FLUID_MINER for _, ek, _ in equipment_rows)
    has_shape_ext = any(
        ek is EquipmentKind.EXTENSION and _extension_surface(lt) == "shape"
        for _, ek, lt in equipment_rows
    )
    has_fluid_ext = any(
        ek is EquipmentKind.EXTENSION and _extension_surface(lt) == "fluid"
        for _, ek, lt in equipment_rows
    )

    shape_eq = has_shape_miner or has_shape_ext
    fluid_eq = has_fluid_miner or has_fluid_ext

    if not has_belt and not has_pipe and not shape_eq and not fluid_eq:
        return SourceKind.RAW_ASTEROID_FIELD, False

    ambiguous = False
    if has_belt and has_pipe:
        return SourceKind.MIXED_EXISTING_LAYOUT, False
    if shape_eq and fluid_eq:
        return SourceKind.MIXED_EXISTING_LAYOUT, False
    if fluid_eq and has_belt and not has_pipe:
        ambiguous = True
        return SourceKind.UNKNOWN, ambiguous
    if shape_eq and has_pipe and not has_belt:
        ambiguous = True
        return SourceKind.UNKNOWN, ambiguous

    if fluid_eq or has_pipe:
        if shape_eq or has_belt:
            return SourceKind.MIXED_EXISTING_LAYOUT, False
        return SourceKind.EXISTING_FLUID_LAYOUT, False

    if shape_eq or has_belt:
        if fluid_eq or has_pipe:
            return SourceKind.MIXED_EXISTING_LAYOUT, False
        return SourceKind.EXISTING_SHAPE_LAYOUT, False

    return SourceKind.UNKNOWN, ambiguous


def _collect_issues(
    *,
    belt_analysis: ExistingTransportAnalysis,
    pipe_analysis: ExistingTransportAnalysis,
    equipment: ExistingEquipmentAnalysis,
    source_ambiguous: bool,
) -> list[ExistingLayoutIssue]:
    issues: list[ExistingLayoutIssue] = []

    def push(
        code: ExistingLayoutIssueCode,
        severity: ExistingLayoutIssueSeverity,
        coords: tuple[Coord, ...],
        component_ids: tuple[int, ...],
        message: str,
    ) -> None:
        issues.append(
            ExistingLayoutIssue(
                code=code,
                severity=severity,
                coords=coords,
                component_ids=component_ids,
                message=message,
            )
        )

    for label, analysis in (("shape_belt", belt_analysis), ("fluid_pipe", pipe_analysis)):
        if analysis.component_count > 1:
            coords = tuple(
                sorted(
                    (c for comp in analysis.components for c in comp.cells),
                    key=lambda c: (c.x, c.y),
                )
            )
            push(
                ExistingLayoutIssueCode.TRANSPORT_DISCONNECTED,
                ExistingLayoutIssueSeverity.WARNING,
                coords,
                tuple(analysis.orphan_component_ids),
                f"{label}: multiple disconnected transport components",
            )
        if analysis.orphan_component_ids:
            oids = frozenset(analysis.orphan_component_ids)
            ocells_list: list[Coord] = []
            for comp in analysis.components:
                if comp.component_id in oids:
                    ocells_list.extend(comp.cells)
            ocells = tuple(sorted(ocells_list, key=lambda c: (c.x, c.y)))
            push(
                ExistingLayoutIssueCode.ORPHAN_TRANSPORT_COMPONENT,
                ExistingLayoutIssueSeverity.WARNING,
                ocells,
                tuple(analysis.orphan_component_ids),
                f"{label}: orphan multi-cell transport components",
            )
        if analysis.single_cell_artifacts:
            push(
                ExistingLayoutIssueCode.SINGLE_CELL_TRANSPORT_ARTIFACT,
                ExistingLayoutIssueSeverity.INFO,
                tuple(sorted(analysis.single_cell_artifacts, key=lambda c: (c.x, c.y))),
                (),
                f"{label}: single-cell transport artifacts",
            )

    if equipment.miners_without_adjacent_transport:
        push(
            ExistingLayoutIssueCode.MINER_NO_ADJACENT_TRANSPORT,
            ExistingLayoutIssueSeverity.WARNING,
            equipment.miners_without_adjacent_transport,
            (),
            "miner missing adjacent correct-kind transport",
        )
    if equipment.miners_attached_to_orphan_transport:
        push(
            ExistingLayoutIssueCode.MINER_ATTACHED_TO_ORPHAN_TRANSPORT,
            ExistingLayoutIssueSeverity.WARNING,
            equipment.miners_attached_to_orphan_transport,
            (),
            "miner adjacent only to non-main / artifact transport",
        )
    if source_ambiguous:
        push(
            ExistingLayoutIssueCode.SOURCE_KIND_AMBIGUOUS,
            ExistingLayoutIssueSeverity.WARNING,
            (),
            (),
            "equipment/transport mix does not admit a single existing-layout class",
        )
    issues.sort(key=lambda i: (i.code.value, i.severity.value, tuple((c.x, c.y) for c in i.coords)))
    return issues


def _build_solver_hints(
    *,
    belt_analysis: ExistingTransportAnalysis,
    pipe_analysis: ExistingTransportAnalysis,
) -> ExistingLayoutSolverHints:
    trunk: set[Coord] = set()
    cleanup: set[Coord] = set()

    for analysis in (belt_analysis, pipe_analysis):
        for comp in analysis.components:
            if comp.status is TransportComponentStatus.MAIN_TRUNK_CANDIDATE:
                trunk.update(comp.cells)
            elif comp.status in (
                TransportComponentStatus.ORPHAN_COMPONENT,
                TransportComponentStatus.SINGLE_CELL_ARTIFACT,
            ):
                cleanup.update(comp.cells)
    return ExistingLayoutSolverHints(
        trunk_seed_cell_union=frozenset(sorted(trunk, key=lambda c: (c.x, c.y))),
        cleanup_candidate_cell_union=frozenset(sorted(cleanup, key=lambda c: (c.x, c.y))),
    )
