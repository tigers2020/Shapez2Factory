"""Parity: append_result, provisional_overlay, and greedy complete replay route cells."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import BundleCellRole
from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    IntegratedRimGreedyResult,
    RimGreedyMetrics,
    RimGreedyPass2Report,
)
from django_apps.asteroid_lab.layers.contracts.rim_greedy_append import AppendCellKind
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.append import (
    append_committed_rim_placements,
    provisional_overlay_from_append,
)
from django_apps.asteroid_lab.replay.event_types import EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
from django_apps.asteroid_lab.replay.layer03_overlay_cells import OVERLAY_KIND_CANDIDATE_ROUTE_PATH
from django_apps.asteroid_lab.replay.layer03_rim_greedy_segment import (
    build_layer03_rim_greedy_runtime_segment_specs,
)
from django_apps.asteroid_lab.replay.runtime_frame_finalize import (
    finalize_segment_spec_to_json_dict,
)
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    renderable_base_map_view_for_golden,
)


def _placements() -> tuple[CommittedRimSeedPlacement, ...]:
    return (
        CommittedRimSeedPlacement(
            placement_id="rim_greedy_CW_TL_0",
            variant_id="CW_TL",
            anchor=(6, 4),
            output_dir="E",
            seed_id="rim_greedy_m1e1",
            miner_cells=frozenset({(6, 4)}),
            extension_cells=frozenset({(5, 4)}),
            m_output_stub=(7, 4),
            route_probe_path=((7, 4), (8, 4), (9, 4)),
        ),
        CommittedRimSeedPlacement(
            placement_id="rim_greedy_CW_TL_1",
            variant_id="CW_TL",
            anchor=(6, 5),
            output_dir="N",
            seed_id="rim_greedy_m1e1",
            miner_cells=frozenset({(6, 5)}),
            extension_cells=frozenset({(6, 4)}),
            m_output_stub=(6, 6),
            route_probe_path=((6, 6), (7, 6)),
        ),
    )


def _integrated_with_append_pipeline() -> IntegratedRimGreedyResult:
    placements = _placements()
    append_result = append_committed_rim_placements(committed_placements=placements)
    overlay = provisional_overlay_from_append(
        append_result,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    return IntegratedRimGreedyResult(
        committed_placements=placements,
        rejected_attempts=(),
        occupied_equipment_cells=frozenset({(6, 4), (5, 4), (6, 5)}),
        reserved_route_cells=frozenset({(8, 4), (9, 4), (6, 6), (7, 6)}),
        append_result=append_result,
        provisional_overlay=overlay,
        pass2_report=RimGreedyPass2Report(
            variant_id="CW_TL",
            score=10.0,
            hard_fail=False,
            miner_count=2,
            extension_count=2,
            total_route_length=5,
        ),
        winning_variant_id="CW_TL",
        metrics=RimGreedyMetrics(
            rim_anchor_count=81,
            committed_placement_count=2,
            rejected_attempt_count=0,
            reserved_route_cell_count=4,
            winning_variant_id="CW_TL",
            pass2_score=10.0,
        ),
        observability_events=(),
    )


def test_layer03_append_overlay_matches_replay_reserved_route_cells() -> None:
    result = _integrated_with_append_pipeline()
    append_route = {
        cell.coord
        for cell in result.append_result.cells
        if cell.kind is AppendCellKind.ROUTE_RESERVED
    }
    overlay_route = {
        coord
        for coord, placed in result.provisional_overlay.by_cell.items()
        if placed.role is BundleCellRole.ROUTE_RESERVED
    }
    assert append_route
    assert append_route == overlay_route

    specs = build_layer03_rim_greedy_runtime_segment_specs(result)
    complete = next(
        spec for spec in specs if spec.event_type.value == EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
    )
    wire = finalize_segment_spec_to_json_dict(
        complete,
        structural_map_view=renderable_base_map_view_for_golden(),
        structural_overlay_wire=(),
        persistent_overlay_wire=(),
        exterior_plan_wire=None,
    )
    replay_route: set[tuple[int, int]] = set()
    for row in wire["map_view"]["overlay_cells"]:
        if not isinstance(row, dict):
            continue
        if str(row.get("kind") or "") != OVERLAY_KIND_CANDIDATE_ROUTE_PATH:
            continue
        replay_route.add((int(row["x"]), int(row["y"])))

    assert replay_route == append_route

    equipment_kinds = {
        str(row.get("kind") or "")
        for row in wire["map_view"]["overlay_cells"]
        if isinstance(row, dict)
    }
    assert "shape_miner" in equipment_kinds
    assert "shape_miner_extension" in equipment_kinds

    by_xy_kind: dict[tuple[int, int, str], int] = {}
    for row in wire["map_view"]["overlay_cells"]:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("kind") or "")
        if kind not in {"shape_miner", "shape_miner_extension"}:
            continue
        by_xy_kind[(int(row["x"]), int(row["y"]), kind)] = int(row.get("rotation") or 0)

    assert by_xy_kind[(6, 5, "shape_miner")] == 3
    assert by_xy_kind[(5, 4, "shape_miner_extension")] == 0
