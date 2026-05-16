"""Pure existing-layout inspection (A6).

Blueprint ``X`` coordinates follow the asteroid map rule: no ``x == 0`` (fixtures use 1, 2, …).
"""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.existing_layout_inspection import inspect_existing_layout


def test_space_pipe_fluid_pipe_components_separate_from_belt() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 3, "Y": 0, "R": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    kinds = {c.transport_kind for c in ins.transport_components}
    assert kinds == {"fluid_pipe", "shape_belt"}
    fluid_pipe = [c for c in ins.transport_components if c.transport_kind == "fluid_pipe"]
    assert all(c.cell_kind == "space_pipe" for c in fluid_pipe)
    shape_belt = [c for c in ins.transport_components if c.transport_kind == "shape_belt"]
    assert all(c.cell_kind == "space_belt" for c in shape_belt)


def test_four_neighbor_grouping_diagonal_does_not_connect() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 2, "Y": 1, "R": 0, "T": "SpacePipe_Right"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    fluid = [c for c in ins.transport_components if c.transport_kind == "fluid_pipe"]
    assert len(fluid) == 2
    assert sorted(c.cell_count for c in fluid) == [1, 1]


def test_main_component_largest_cell_count_wins() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 2, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
                {"X": 6, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 7, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
                {"X": 8, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    fluid = [c for c in ins.transport_components if c.transport_kind == "fluid_pipe"]
    assert len(fluid) == 2
    main = ins.hints_json["main_component_candidate"]["fluid_pipe"]
    assert main["cell_count"] == 3
    assert main["component_id"] == max(c.component_id for c in fluid if c.cell_count == 3)


def test_main_component_tie_breaks_on_lower_component_id() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 4, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    fluid = [c for c in ins.transport_components if c.transport_kind == "fluid_pipe"]
    assert len(fluid) == 2
    assert all(c.cell_count == 1 for c in fluid)
    main_id = ins.hints_json["main_component_candidate"]["fluid_pipe"]["component_id"]
    assert main_id == min(c.component_id for c in fluid)


def test_two_clusters_orphan_and_transport_disconnected() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 2, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
                {"X": 6, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    fluid = [c for c in ins.transport_components if c.transport_kind == "fluid_pipe"]
    assert len(fluid) == 2
    main_id = ins.hints_json["main_component_candidate"]["fluid_pipe"]["component_id"]
    main_comp = next(c for c in fluid if c.component_id == main_id)
    assert main_comp.cell_count == 2
    orphan = next(c for c in fluid if c.component_id != main_id)
    assert orphan.cell_count == 1
    assert any(i.issue_code == "transport_disconnected" for i in ins.issues)
    cleanup = ins.hints_json["cleanup_candidate_cells"]
    assert len(cleanup) == 1


def test_fluid_miner_and_extension_indexed() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "R": 0, "T": "Layout_FluidMinerExtension"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    kinds = {e.cell_kind for e in ins.equipment}
    assert kinds == {"fluid_miner", "fluid_miner_extension"}


def test_shape_miner_indexed_when_present() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 1, "R": 0, "T": "Layout_ShapeMinerExtension"},
                {"X": 2, "Y": 0, "R": 0, "T": "SpaceBelt_Left"},
                {"X": 2, "Y": 1, "R": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert {e.cell_kind for e in ins.equipment} >= {"shape_miner", "shape_miner_extension"}


def test_miner_adjacent_transport_attaches_to_component() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 1, "Y": 1, "R": 0, "T": "Layout_FluidMiner"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    att = next(a for a in ins.attachments if a.equipment_id == "1,1,null")
    assert att.attached_to_any_transport is True
    assert att.attached_to_main_component is True
    assert not any(i.issue_code == "miner_no_adjacent_transport" for i in ins.issues)


def test_miner_no_adjacent_transport_issue() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 0, "R": 0, "T": "Layout_FluidMiner"}],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert any(i.issue_code == "miner_no_adjacent_transport" for i in ins.issues)


def test_extension_no_adjacent_transport_issue() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 0, "R": 0, "T": "Layout_FluidMinerExtension"}],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert any(i.issue_code == "extension_no_adjacent_transport" for i in ins.issues)


def test_miner_attached_only_to_orphan_transport() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 2, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
                {"X": 6, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 6, "Y": 1, "R": 0, "T": "Layout_FluidMiner"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert any(i.issue_code == "miner_attached_to_orphan_transport" for i in ins.issues)
    att = next(i for i in ins.issues if i.issue_code == "miner_attached_to_orphan_transport")
    assert len(att.cells_json) >= 2
    assert att.cells_json[0].get("cell_kind") == "fluid_miner"
    assert all(
        c.get("cell_kind") in ("space_pipe", "space_belt") for c in att.cells_json[1:]
    )


def test_mixed_transport_nearby() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_FluidMiner"},
                {"X": 1, "Y": 1, "R": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert any(i.issue_code == "mixed_transport_nearby" for i in ins.issues)


def test_nested_b_entries_not_unfolded_single_top_level_cell() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {
                    "X": 1,
                    "Y": 0,
                    "R": 0,
                    "T": "Layout_FluidMiner",
                    "B": {
                        "$type": "Building",
                        "Entries": [{"X": 1, "Y": 1, "T": "PumpDefaultInternalVariant"}],
                    },
                },
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert len(snap.cells) == 1
    assert len(ins.equipment) == 1


def test_hints_contain_main_component_candidate_and_cleanup_candidates() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 4, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    assert "main_component_candidate" in ins.hints_json
    assert "fluid_pipe" in ins.hints_json["main_component_candidate"]
    assert "cleanup_candidate_cells" in ins.hints_json
    assert len(ins.hints_json["cleanup_candidate_cells"]) >= 1
