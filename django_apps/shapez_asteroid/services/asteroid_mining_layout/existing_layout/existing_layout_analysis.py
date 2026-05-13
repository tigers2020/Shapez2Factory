"""STEP 0.5 — Existing layout analysis (read-only context for decode / solver / UI).

See ``documents/Algorithm/mining_solver_cursor_sessions/03_data_schema_dto.md`` §E.
Does not mutate maps or change Pass3 / reclaim policy.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, cast

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.existing_layout_types import (
    ExistingLayoutAnalysisWire,
    ExistingLayoutIssueWire,
    ExistingTransportAnalysisWire,
    ExistingTransportComponentWire,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.mining_map_cell import (
    MiningMapCellsByCoord,
    MiningMapRows,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_components import (  # noqa: E501
    bbox_of_cells,
    cell_component_maps,
    components_for_role,
    coord_key,
    neighbor_transport_cells,
    role_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    blocked_cells,
    layout_kind,
    transport_kind_for_extractor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    external_predicate_for_mining_map,
    mineable_bbox,
    transport_cells_reaching_external,
)

SourceKind = Literal[
    "raw_asteroid_field",
    "existing_fluid_layout",
    "existing_shape_layout",
    "mixed_existing_layout",
    "unknown",
]

IssueCode = Literal[
    "TRANSPORT_DISCONNECTED",
    "ORPHAN_TRANSPORT_COMPONENT",
    "SINGLE_CELL_TRANSPORT_ARTIFACT",
    "MINER_NO_ADJACENT_TRANSPORT",
    "MINER_ATTACHED_TO_ORPHAN_TRANSPORT",
    "SOURCE_KIND_AMBIGUOUS",
]


def _infer_source_kind(
    cells: MiningMapCellsByCoord,
    *,
    has_belt: bool,
    has_pipe: bool,
) -> SourceKind:
    shape_n = 0
    fluid_n = 0
    ext_n = 0
    for row in cells.values():
        if row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE:
            shape_n += 1
        elif lk in EXTRACTORS_FLUID:
            fluid_n += 1
        elif lk in EXTENSIONS:
            ext_n += 1

    has_transport = has_belt or has_pipe
    has_mining = shape_n > 0 or fluid_n > 0 or ext_n > 0

    if not has_transport and has_mining:
        return "raw_asteroid_field"
    if not has_mining and not has_transport:
        return "unknown"
    if not has_transport:
        return "unknown"

    if shape_n > 0 and fluid_n > 0:
        return "mixed_existing_layout"
    if fluid_n > 0:
        return "existing_fluid_layout"
    if shape_n > 0:
        return "existing_shape_layout"
    if ext_n > 0 and shape_n == 0 and fluid_n == 0:
        if has_belt and not has_pipe:
            return "existing_shape_layout"
        if has_pipe and not has_belt:
            return "existing_fluid_layout"
        if has_belt and has_pipe:
            return "mixed_existing_layout"
    return "unknown"


def _analyze_one_transport_kind(
    kind_key: Literal["shape_belt", "fluid_pipe"],
    role: str,
    cells: MiningMapCellsByCoord,
    reaching: set[Coord],
) -> ExistingTransportAnalysisWire:
    tset = role_transport_cells(cells, role)
    comps = components_for_role(tset)
    comp_reaches = [bool(c & reaching) for c in comps]

    main_id: int | None = None
    best: frozenset[Coord] | None = None
    for i, c in enumerate(comps):
        if not comp_reaches[i]:
            continue
        if best is None or len(c) > len(best):
            best = c
            main_id = i
        elif len(c) == len(best) and coord_key(min(c)) < coord_key(min(best)):
            best = c
            main_id = i

    orphan_ids = [i for i, c in enumerate(comps) if not comp_reaches[i] and len(c) >= 2]
    single_ids = [i for i, c in enumerate(comps) if len(c) == 1]

    single_cell_coords: list[list[int]] = []
    for i in single_ids:
        comp = comps[i]
        if len(comp) != 1:
            continue
        p = next(iter(comp))
        single_cell_coords.append([p[0], p[1]])
    single_cell_coords.sort(key=lambda q: (q[1], q[0]))

    summaries: list[ExistingTransportComponentWire] = []
    for i, c in enumerate(comps):
        x0, x1, y0, y1 = bbox_of_cells(c)
        touches = comp_reaches[i]
        if len(c) == 1:
            status: str = "single_cell_artifact"
        elif not touches:
            status = "orphan_component"
        elif i == main_id:
            status = "main_trunk_candidate"
        else:
            status = "cleanup_candidate"
        summaries.append(
            {
                "component_id": i,
                "kind": kind_key,
                "cells": [[x, y] for x, y in sorted(c, key=coord_key)],
                "cell_count": len(c),
                "bbox": {"x_min": x0, "x_max": x1, "y_min": y0, "y_max": y1},
                "touches_external_margin": touches,
                "status": status,
            }
        )

    return {
        "transport_kind": kind_key,
        "component_count": len(comps),
        "main_component_id": main_id,
        "components": summaries,
        "orphan_component_ids": orphan_ids,
        "single_cell_artifacts": single_cell_coords,
    }


def analyze_existing_layout_from_mining_map(
    mining_map: MiningMapRows,
    *,
    is_external: Callable[[Coord], bool] | None = None,
) -> dict[str, Any]:
    """Return JSON-friendly ExistingLayoutAnalysis (§E.3) for maps that may include transport."""

    cells = cells_dict_from_mining_map(mining_map)
    belt_cells = role_transport_cells(cells, "belt")
    pipe_cells = role_transport_cells(cells, "pipe")
    has_belt = bool(belt_cells)
    has_pipe = bool(pipe_cells)
    source_kind = _infer_source_kind(cells, has_belt=has_belt, has_pipe=has_pipe)

    ext_pred = is_external or external_predicate_for_mining_map(mining_map)
    all_transport = belt_cells | pipe_cells
    blocked = blocked_cells(cells)
    reaching = transport_cells_reaching_external(all_transport, blocked, ext_pred)

    transport_blocks: dict[str, ExistingTransportAnalysisWire] = {}
    if has_belt:
        transport_blocks["shape_belt"] = _analyze_one_transport_kind(
            "shape_belt", "belt", cells, reaching
        )
    if has_pipe:
        transport_blocks["fluid_pipe"] = _analyze_one_transport_kind(
            "fluid_pipe", "pipe", cells, reaching
        )

    transport_primary: ExistingTransportAnalysisWire
    if has_belt and not has_pipe:
        transport_primary = transport_blocks["shape_belt"]
    elif has_pipe and not has_belt:
        transport_primary = transport_blocks["fluid_pipe"]
    elif has_belt and has_pipe:
        transport_primary = {
            "transport_kind": "mixed",
            "component_count": transport_blocks["shape_belt"]["component_count"]
            + transport_blocks["fluid_pipe"]["component_count"],
            "main_component_id": None,
            "components": [],
            "orphan_component_ids": [],
            "single_cell_artifacts": [],
            "by_kind": transport_blocks,
        }
    else:
        transport_primary = {
            "transport_kind": "none",
            "component_count": 0,
            "main_component_id": None,
            "components": [],
            "orphan_component_ids": [],
            "single_cell_artifacts": [],
        }

    miner_count = 0
    extension_count = 0
    miners_no_adj_set: set[tuple[int, int]] = set()
    miners_orphan_set: set[tuple[int, int]] = set()

    belt_cell_to_id, belt_by_id = cell_component_maps(
        components_for_role(belt_cells) if belt_cells else []
    )
    pipe_cell_to_id, pipe_by_id = cell_component_maps(
        components_for_role(pipe_cells) if pipe_cells else []
    )

    for c, row in cells.items():
        lk = layout_kind(row)
        if row.get("role") != "occupied":
            continue
        if lk in EXTENSIONS:
            extension_count += 1
        if lk not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            continue
        miner_count += 1
        tk = transport_kind_for_extractor(row)
        if tk is None:
            continue
        raw_r = row.get("r")
        stub_cells: list[Coord] = []
        if isinstance(raw_r, int):
            stub = shape_miner_output_cell(c, raw_r)
            if stub is not None:
                stub_cells = [stub]
        else:
            stub_cells = neighbor_transport_cells(cells, c, tk)

        if not stub_cells:
            miners_no_adj_set.add((c[0], c[1]))
            continue

        stub_ok = False
        for stub in stub_cells:
            row_s = cells.get(stub)
            ok = row_s is not None and (
                (tk == "shape_belt" and row_s.get("role") == "belt")
                or (tk == "fluid_pipe" and row_s.get("role") == "pipe")
            )
            if ok:
                stub_ok = True
                break
        if not stub_ok:
            miners_no_adj_set.add((c[0], c[1]))
            continue

        orphan_hit = False
        for stub in stub_cells:
            if tk == "shape_belt" and stub in belt_cell_to_id:
                cid = belt_cell_to_id[stub]
                comp = belt_by_id[cid]
                if not (comp & reaching):
                    orphan_hit = True
            elif tk == "fluid_pipe" and stub in pipe_cell_to_id:
                cid = pipe_cell_to_id[stub]
                comp = pipe_by_id[cid]
                if not (comp & reaching):
                    orphan_hit = True
        if orphan_hit:
            miners_orphan_set.add((c[0], c[1]))

    miners_no_adj = [[x, y] for x, y in sorted(miners_no_adj_set, key=lambda p: (p[1], p[0]))]
    miners_orphan = [[x, y] for x, y in sorted(miners_orphan_set, key=lambda p: (p[1], p[0]))]

    bbox = mineable_bbox(cells)
    island_bbox = (
        {"x_min": bbox[0], "x_max": bbox[1], "y_min": bbox[2], "y_max": bbox[3]} if bbox else None
    )

    issues: list[ExistingLayoutIssueWire] = []

    def _add_issue(
        code: IssueCode,
        severity: Literal["info", "warning", "error"],
        coords: list[list[int]],
        message: str,
        component_ids: list[int] | None = None,
    ) -> None:
        issues.append(
            {
                "code": code,
                "severity": severity,
                "coords": coords,
                "component_ids": component_ids or [],
                "message": message,
            }
        )

    if source_kind == "unknown":
        _add_issue(
            "SOURCE_KIND_AMBIGUOUS",
            "info",
            [],
            (
                "Could not classify raw asteroid vs existing layout from transport "
                "+ equipment pattern."
            ),
        )

    for block in transport_blocks.values():
        if not isinstance(block, dict) or "components" not in block:
            continue
        for comp_row in block["components"]:
            st = comp_row.get("status")
            if st == "orphan_component":
                cell_pairs = comp_row.get("cells") or []
                _add_issue(
                    "ORPHAN_TRANSPORT_COMPONENT",
                    "warning",
                    cell_pairs[:50],
                    (
                        f"Orphan {block.get('transport_kind')} "
                        f"component id={comp_row.get('component_id')}"
                    ),
                    component_ids=[int(comp_row.get("component_id", -1))],
                )
            if st == "single_cell_artifact":
                cell_pairs = comp_row.get("cells") or []
                _add_issue(
                    "SINGLE_CELL_TRANSPORT_ARTIFACT",
                    "info",
                    cell_pairs,
                    (
                        f"Single-cell {block.get('transport_kind')} "
                        f"artifact id={comp_row.get('component_id')}"
                    ),
                    component_ids=[int(comp_row.get("component_id", -1))],
                )

    for xy in miners_no_adj:
        _add_issue(
            "MINER_NO_ADJACENT_TRANSPORT",
            "warning",
            [xy],
            "Extractor has no valid adjacent transport / stub for its kind.",
        )
    for xy in miners_orphan:
        _add_issue(
            "MINER_ATTACHED_TO_ORPHAN_TRANSPORT",
            "warning",
            [xy],
            "Extractor stub touches transport not reaching external margin.",
        )

    trunk_seed: set[Coord] = set()
    cleanup: set[Coord] = set()
    for block in transport_blocks.values():
        if not isinstance(block, dict):
            continue
        for comp_row in block.get("components") or []:
            st2 = comp_row.get("status")
            cells_l = comp_row.get("cells") or []
            parsed = {(p[0], p[1]) for p in cells_l if len(p) >= 2}
            if st2 == "main_trunk_candidate":
                trunk_seed |= parsed
            elif st2 in ("orphan_component", "single_cell_artifact", "cleanup_candidate"):
                cleanup |= parsed

    wire = cast(
        ExistingLayoutAnalysisWire,
        {
            "source_kind": source_kind,
            "island_bbox": island_bbox,
            "transport": transport_primary,
            "transport_by_kind": transport_blocks if len(transport_blocks) > 1 else None,
            "equipment": {
                "miner_count": miner_count,
                "extension_count": extension_count,
                "miners_without_adjacent_transport": miners_no_adj,
                "miners_attached_to_orphan_transport": miners_orphan,
                "equipment_attachment": [],
            },
            "issues": issues,
            "solver_hints": {
                "trunk_seed_cell_union": [[x, y] for x, y in sorted(trunk_seed, key=coord_key)],
                "cleanup_candidate_cell_union": [[x, y] for x, y in sorted(cleanup, key=coord_key)],
            },
        },
    )
    return dict(wire)


def existing_layout_heuristic_suppress_pass12_loops(
    existing_layout_analysis: ExistingLayoutAnalysisWire | dict[str, Any] | None,
) -> bool:
    """Return True to skip Pass1/Pass2 placement loops while keeping STEP4 (preserve-first).

    Conservative: requires classified existing layout, main transport trunk, miners+extensions,
    and no STEP 0.5 issues at severity ``error``.
    """

    if not existing_layout_analysis or not isinstance(existing_layout_analysis, dict):
        return False
    sk = existing_layout_analysis.get("source_kind")
    if sk in ("raw_asteroid_field", "unknown", "mixed_existing_layout"):
        return False
    eq = existing_layout_analysis.get("equipment") or {}
    if int(eq.get("miner_count") or 0) <= 0:
        return False
    if int(eq.get("extension_count") or 0) <= 0:
        return False
    tp = existing_layout_analysis.get("transport") or {}
    if not isinstance(tp, dict) or tp.get("main_component_id") is None:
        return False
    for iss in existing_layout_analysis.get("issues") or []:
        if isinstance(iss, dict) and iss.get("severity") == "error":
            return False
    return True


def effective_suppress_pass1_loop(
    existing_layout_analysis: ExistingLayoutAnalysisWire | dict[str, Any] | None,
) -> bool:
    """Whether the Pass1 outer placement loop should be skipped.

    ``existing_fluid_layout`` always suppresses Pass1 (preserve-first guard). Other
    classifications follow the conservative heuristic.
    """

    if isinstance(existing_layout_analysis, dict):
        if existing_layout_analysis.get("source_kind") == "existing_fluid_layout":
            return True
    return existing_layout_heuristic_suppress_pass12_loops(existing_layout_analysis)


def effective_suppress_pass2_loop(
    existing_layout_analysis: ExistingLayoutAnalysisWire | dict[str, Any] | None,
) -> bool:
    """Whether the Pass2 internal placement loop should be skipped.

    For ``existing_fluid_layout``, Pass2 stays suppressed by default to preserve legacy
    behavior; setting ``SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED=1`` re-enables
    Pass2 so internal mineable voids can be filled while preserve bundles stay protected
    via ``blocked_cells``. Other classifications follow the conservative heuristic.
    """

    if isinstance(existing_layout_analysis, dict):
        if existing_layout_analysis.get("source_kind") == "existing_fluid_layout":
            from django.conf import settings

            if getattr(settings, "SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED", False):
                return False
            return True
    return existing_layout_heuristic_suppress_pass12_loops(existing_layout_analysis)


def effective_suppress_pass12_placement_loops(
    existing_layout_analysis: ExistingLayoutAnalysisWire | dict[str, Any] | None,
) -> bool:
    """Whether both Pass1 and Pass2 loops should be skipped (legacy aggregate flag)."""

    sp1 = effective_suppress_pass1_loop(existing_layout_analysis)
    sp2 = effective_suppress_pass2_loop(existing_layout_analysis)
    return sp1 and sp2


__all__ = [
    "analyze_existing_layout_from_mining_map",
    "effective_suppress_pass12_placement_loops",
    "effective_suppress_pass1_loop",
    "effective_suppress_pass2_loop",
    "existing_layout_heuristic_suppress_pass12_loops",
]
