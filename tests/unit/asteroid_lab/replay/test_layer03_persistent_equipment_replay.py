"""L3 committed miner+extension overlays persist through L4 transport replay frames."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_COMPLETE,
)
from django_apps.asteroid_lab.replay.layer03_rim_greedy_segment import (
    COMMITTED_RIM_EQUIPMENT_OVERLAY_ROLE,
    build_persistent_committed_equipment_overlay_wire,
)
from django_apps.asteroid_lab.replay.solver_runtime_assembler import (
    build_solver_runtime_replay_frames,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy_append import (
    LAYER_03_APPEND_SOURCE,
    AppendCellKind,
    AppendedPlacementCell,
    Layer03AppendResult,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import golden_5x5_complete_map
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    exterior_plan_wire_for_golden,
    layer04_route_plan_with_transport_tiles_for_golden,
    reconstruction_complete_lab_frame_dict_for_golden,
)


def _rim_with_miner_and_extension() -> object:
    placement = CommittedRimSeedPlacement(
        placement_id="p0",
        variant_id="v1",
        anchor=(0, 0),
        output_dir="E",
        seed_id="gene_a",
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset({(-1, 0)}),
        m_output_stub=(1, 0),
        throughput_factor=16,
        route_probe_path=(),
    )
    append = Layer03AppendResult(
        cells=(
            AppendedPlacementCell(
                coord=(0, 0),
                kind=AppendCellKind.MINER,
                placement_id="p0",
                variant_id="v1",
                source_layer=LAYER_03_APPEND_SOURCE,
            ),
            AppendedPlacementCell(
                coord=(-1, 0),
                kind=AppendCellKind.EXTENSION,
                placement_id="p0",
                variant_id="v1",
                source_layer=LAYER_03_APPEND_SOURCE,
            ),
        ),
        placement_count=1,
        route_reserved_cell_count=0,
        source_layer=LAYER_03_APPEND_SOURCE,
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        append_result=append,
    )


def test_persistent_equipment_wire_includes_miner_and_extension_kinds() -> None:
    wire = build_persistent_committed_equipment_overlay_wire(_rim_with_miner_and_extension())
    kinds = {str(row.get("kind")) for row in wire}
    roles = {str(row.get("overlay_role")) for row in wire}
    assert kinds == {"shape_miner", "shape_miner_extension"}
    assert roles == {COMMITTED_RIM_EQUIPMENT_OVERLAY_ROLE}


def test_l4_transport_complete_frame_carries_committed_equipment() -> None:
    frames = build_solver_runtime_replay_frames(
        complete_map=golden_5x5_complete_map(),
        lab_frames_before_append=[reconstruction_complete_lab_frame_dict_for_golden()],
        exterior_plan_wire=exterior_plan_wire_for_golden(),
        layer03=_rim_with_miner_and_extension(),
        layer04=None,
        layer05_route_plan=layer04_route_plan_with_transport_tiles_for_golden(),
    )
    complete = next(
        f for f in frames if f["event_type"] == EVENT_TYPE_LAYER05_TRANSPORT_ROUTING_COMPLETE
    )
    overlay = (complete.get("map_view") or {}).get("overlay_cells") or []
    kinds = {str(row.get("kind")) for row in overlay}
    assert "shape_miner" in kinds
    assert "shape_miner_extension" in kinds
    assert any(str(row.get("kind", "")).startswith("space_") for row in overlay)
