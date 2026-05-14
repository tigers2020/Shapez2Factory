"""STEP 0.5 read-only analysis contracts (no mineable cells, no blueprint mutation)."""

from __future__ import annotations

import base64
import gzip
import json

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    analyze_decoded_layout,
    compute_transport_components,
    decode_copy_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    FinalValidationReport,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    SourceKind,
    TransportComponentStatus,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_json import (
    existing_layout_analysis_to_json,
)


def test_empty_decoded_is_raw_asteroid_field_and_has_no_mineable() -> None:
    decoded: dict = {"BP": {"Entries": []}}
    before = decoded["BP"]["Entries"] is not None
    analysis = analyze_decoded_layout(decoded)
    assert before
    assert analysis.source_kind is SourceKind.RAW_ASTEROID_FIELD
    assert decoded == {"BP": {"Entries": []}}
    assert analysis.solver_hints.trunk_seed_cell_union == frozenset()


def test_raw_asteroid_shell_only_not_classified_as_existing_layout() -> None:
    """Asteroid field entries without miners/belt/pipe stay raw (not forced existing layout)."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 2, "T": "AsteroidField_Some"},
                {"X": 3, "Y": 2, "T": "UnknownThing"},
            ]
        }
    }
    analysis = analyze_decoded_layout(decoded)
    assert analysis.source_kind is SourceKind.RAW_ASTEROID_FIELD


def test_fluid_miner_and_space_pipe_is_existing_fluid_layout() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 1, "T": "SpacePipe_Straight"},
                {"X": 3, "Y": 1, "T": "SpacePipe_Straight"},
                {"X": 4, "Y": 1, "T": "SpacePipe_Straight"},
            ]
        }
    }
    analysis = analyze_decoded_layout(decoded)
    assert analysis.source_kind is SourceKind.EXISTING_FLUID_LAYOUT
    assert analysis.belt_transport.component_count == 0
    assert analysis.pipe_transport.component_count == 1
    assert analysis.pipe_transport.main_component_id == 0


def test_main_pipe_component_cells_in_trunk_seed_not_in_cleanup() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 1, "T": "SpacePipe_Straight"},
                {"X": 3, "Y": 1, "T": "SpacePipe_Straight"},
            ]
        }
    }
    analysis = analyze_decoded_layout(decoded)
    trunk = analysis.solver_hints.trunk_seed_cell_union
    cleanup = analysis.solver_hints.cleanup_candidate_cell_union
    assert Coord(2, 1) in trunk and Coord(3, 1) in trunk
    assert trunk.isdisjoint(cleanup)


def test_orphan_pipe_component_in_cleanup_not_trunk_seed() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 1, "T": "SpacePipe_Straight"},
                {"X": 3, "Y": 1, "T": "SpacePipe_Straight"},
                {"X": 10, "Y": 10, "T": "SpacePipe_Straight"},
                {"X": 11, "Y": 10, "T": "SpacePipe_Straight"},
            ]
        }
    }
    analysis = analyze_decoded_layout(decoded)
    trunk = analysis.solver_hints.trunk_seed_cell_union
    cleanup = analysis.solver_hints.cleanup_candidate_cell_union
    assert Coord(10, 10) in cleanup and Coord(11, 10) in cleanup
    assert Coord(10, 10) not in trunk and Coord(11, 10) not in trunk
    assert Coord(2, 1) in trunk


def test_single_cell_pipe_is_cleanup_candidate_not_trunk() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 5, "Y": 5, "T": "SpacePipe_Straight"},
            ]
        }
    }
    analysis = analyze_decoded_layout(decoded)
    assert analysis.pipe_transport.component_count == 1
    st0 = analysis.pipe_transport.components[0].status
    assert st0 is TransportComponentStatus.SINGLE_CELL_ARTIFACT
    assert analysis.solver_hints.trunk_seed_cell_union == frozenset()
    assert Coord(5, 5) in analysis.solver_hints.cleanup_candidate_cell_union


def test_existing_layout_analysis_has_no_mineable_field() -> None:
    analysis = analyze_decoded_layout({"BP": {"Entries": []}})
    assert not hasattr(analysis, "mineable_placement_cells")
    assert "mineable_placement_cells" not in analysis.__dataclass_fields__


def test_json_report_top_level_keys_are_existing_layout_prefixed() -> None:
    analysis = analyze_decoded_layout({"BP": {"Entries": []}})
    payload = existing_layout_analysis_to_json(analysis)
    fv_fields = {f.name for f in FinalValidationReport.__dataclass_fields__.values()}
    assert fv_fields.isdisjoint(set(payload.keys()))
    assert "existing_layout_source_kind" in payload
    assert "existing_layout_solver_hints" in payload
    assert "geometry_ok" not in payload


def test_belt_and_pipe_analyses_are_separate() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 2, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 1, "T": "Belt_Straight"},
                {"X": 4, "Y": 1, "T": "Belt_Straight"},
                {"X": 2, "Y": 3, "T": "SpacePipe_Straight"},
                {"X": 3, "Y": 3, "T": "SpacePipe_Straight"},
            ]
        }
    }
    analysis = analyze_decoded_layout(decoded)
    assert analysis.source_kind is SourceKind.MIXED_EXISTING_LAYOUT
    assert analysis.belt_transport.transport_kind is TransportKind.SHAPE_BELT
    assert analysis.pipe_transport.transport_kind is TransportKind.FLUID_PIPE
    assert analysis.belt_transport.component_count == 1
    assert analysis.pipe_transport.component_count == 1


def test_compute_transport_components_4_neighbor_same_kind() -> None:
    cells = frozenset({Coord(1, 1), Coord(2, 1), Coord(5, 5)})
    comps = compute_transport_components(cells, TransportKind.SHAPE_BELT)
    assert len(comps) == 2
    assert frozenset({Coord(1, 1), Coord(2, 1)}) in comps
    assert frozenset({Coord(5, 5)}) in comps


def test_decode_copy_payload_accepts_shapez2_v4_roundtrip() -> None:
    root = {"BP": {"Entries": [{"X": 2, "Y": 2, "T": "Layout_ShapeMiner"}]}}
    raw = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(raw)
    b64 = base64.b64encode(gz).decode("ascii").rstrip("=")
    code = "SHAPEZ2-4-" + b64
    doc = decode_copy_payload(code)
    assert doc.as_mutable_dict()["BP"]["Entries"][0]["T"] == "Layout_ShapeMiner"


def test_decode_copy_payload_mapping_does_not_mutate_caller_dict() -> None:
    inner = {"BP": {"Entries": []}}
    doc = decode_copy_payload(inner)
    _ = doc
    assert inner["BP"]["Entries"] == []
