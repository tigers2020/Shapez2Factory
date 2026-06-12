"""L3 committed miner+extension overlays persist through L4 transport replay frames."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

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
from shapez2_factory.adapters.asteroid_lab.runtime_wires.deserialize import deserialize_l3_wire
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

_RUN7_WIRES = (
    Path(__file__).resolve().parents[4]
    / "var/runs/asteroid-1-6b9854f689c34b80988298537e6022cf/output/solver_runtime_wires.v1.json"
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


def test_persistent_equipment_wire_rebuilds_when_append_cells_missing() -> None:
    placement = CommittedRimSeedPlacement(
        placement_id="p0",
        variant_id="v1",
        anchor=(-4, -13),
        output_dir="n",
        seed_id="gene_a",
        miner_cells=frozenset({(-4, -13)}),
        extension_cells=frozenset({(-4, -12)}),
        m_output_stub=(-4, -14),
        throughput_factor=16,
        route_probe_path=(),
    )
    result = replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        reserved_route_cells=frozenset(),
    )
    wire = build_persistent_committed_equipment_overlay_wire(result)
    by_coord = {(int(row["x"]), int(row["y"])): row for row in wire}
    assert by_coord[(-4, -13)]["kind"] == "shape_miner"
    assert by_coord[(-4, -13)]["rotation"] == 3
    assert by_coord[(-4, -12)]["kind"] == "shape_miner_extension"
    assert by_coord[(-4, -12)]["rotation"] != 0


def test_deserialized_run7_wire_projects_committed_equipment_not_candidate_miner() -> None:
    if not _RUN7_WIRES.is_file():
        return
    wires = json.loads(_RUN7_WIRES.read_text(encoding="utf-8"))
    l3wire = wires["layers"]["layer_03_rim_greedy_placement"]
    result = deserialize_l3_wire(l3wire)
    assert result.append_result.cells
    wire = build_persistent_committed_equipment_overlay_wire(result)
    kinds = {str(row.get("kind")) for row in wire if row.get("overlay_role")}
    assert "candidate_miner" not in kinds
    assert "shape_miner" in kinds
    assert "shape_miner_extension" in kinds
    rotations = {int(row.get("rotation", 0)) for row in wire if row.get("kind") == "shape_miner"}
    assert rotations != {0}


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
