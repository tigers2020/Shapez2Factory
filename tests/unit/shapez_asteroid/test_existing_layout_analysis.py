from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout import (
    existing_layout_components as elc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
    validate_final_mining_layout,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    build_map_timeline,
    merge_with_transport_and_final_mining_map,
)


def test_raw_asteroid_no_transport_classifies_raw_field() -> None:
    mining_map = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "r": 0,
        },
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    assert out["source_kind"] == "raw_asteroid_field"
    assert out["transport"]["transport_kind"] == "none"


def test_existing_layout_fields_do_not_leak_into_final_validation_report() -> None:
    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    before = deepcopy(mining_map)
    ela = analyze_existing_layout_from_mining_map(mining_map)
    report = validate_final_mining_layout(mining_map)
    final_fields = set(asdict(report))
    assert "source_kind" in ela
    assert "solver_hints" in ela
    assert "source_kind" not in final_fields
    assert "solver_hints" not in final_fields
    assert "existing_layout_orphan_transport_cell_count" not in final_fields
    assert mining_map == before


def test_belt_single_component_classifies_shape_layout() -> None:
    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    assert out["source_kind"] == "existing_shape_layout"
    belt = out["transport"]
    assert belt["component_count"] == 1
    st = belt["components"][0]["status"]
    assert st in ("main_trunk_candidate", "orphan_component", "cleanup_candidate")


def test_step05_merge_baseline_includes_inferred_for_analysis() -> None:
    """STEP 0.5 uses merged with_transport + final map (same contract as solver_init)."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 10, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
            ]
        }
    }
    tl = build_map_timeline(decoded)
    merged = merge_with_transport_and_final_mining_map(tl[0]["mining_map"], tl[-1]["mining_map"])
    assert any(c.get("role") == "inferred" for c in merged)
    is_ext = external_predicate_for_mining_map(tl[1]["mining_map"])
    out = analyze_existing_layout_from_mining_map(merged, is_external=is_ext)
    assert "source_kind" in out
    assert "transport" in out


def test_isolated_belt_component_is_orphan_issue() -> None:
    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 80, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 81, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    codes = {i["code"] for i in out["issues"]}
    assert "ORPHAN_TRANSPORT_COMPONENT" in codes


def test_ela_trunk_seed_excludes_orphan_belt_cells() -> None:
    """Orphan belt component cells belong in cleanup union only, not trunk_seed (PR4-C)."""

    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 4, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 5, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 80, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 81, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    sh = out["solver_hints"]
    trunk = {(int(p[0]), int(p[1])) for p in sh["trunk_seed_cell_union"]}
    cleanup = {(int(p[0]), int(p[1])) for p in sh["cleanup_candidate_cell_union"]}
    assert (80, 80) in cleanup and (81, 80) in cleanup
    assert (80, 80) not in trunk and (81, 80) not in trunk
    assert (2, 1) in trunk


def test_role_transport_cells_separates_inferred_belt_vs_pipe() -> None:
    """Inferred segment rows map to one ``want_role`` only (no mixed trunk collection)."""

    cells = {
        (1, 1): {
            "x": 1,
            "y": 1,
            "role": "inferred",
            "layout_kind": "shape_belt_segment",
            "surface": "shape",
        },
        (2, 1): {
            "x": 2,
            "y": 1,
            "role": "inferred",
            "layout_kind": "fluid_pipe_segment",
            "surface": "fluid",
        },
    }
    belts = elc.role_transport_cells(cells, "belt")
    pipes = elc.role_transport_cells(cells, "pipe")
    assert (1, 1) in belts and (1, 1) not in pipes
    assert (2, 1) in pipes and (2, 1) not in belts


def test_ela_inferred_fluid_pipe_main_trunk_in_trunk_seed() -> None:
    """Merged-style inferred ``fluid_pipe_segment`` participates in main pipe trunk + ELA seed."""

    mining_map = [
        {
            "x": 1,
            "y": 0,
            "role": "occupied",
            "surface": "fluid",
            "layout_kind": "fluid_extension",
        },
        {
            "x": 5,
            "y": 0,
            "role": "inferred",
            "surface": "fluid",
            "layout_kind": "fluid_pipe_segment",
        },
        {
            "x": 6,
            "y": 0,
            "role": "inferred",
            "surface": "fluid",
            "layout_kind": "fluid_pipe_segment",
        },
        {
            "x": 7,
            "y": 0,
            "role": "inferred",
            "surface": "fluid",
            "layout_kind": "fluid_pipe_segment",
        },
    ]

    def _is_ext(c: tuple[int, int]) -> bool:
        return c == (8, 0)

    out = analyze_existing_layout_from_mining_map(mining_map, is_external=_is_ext)
    assert out["source_kind"] == "existing_fluid_layout"
    trunk = {(int(p[0]), int(p[1])) for p in out["solver_hints"]["trunk_seed_cell_union"]}
    assert {(5, 0), (6, 0), (7, 0)}.issubset(trunk)


def test_ela_single_inferred_fluid_pipe_artifact_not_in_trunk_seed() -> None:
    """Single-cell inferred pipe stays ``single_cell_artifact`` / cleanup only (not promoted)."""

    mining_map = [
        {
            "x": 1,
            "y": 0,
            "role": "occupied",
            "surface": "fluid",
            "layout_kind": "fluid_extension",
        },
        {
            "x": 50,
            "y": 50,
            "role": "inferred",
            "surface": "fluid",
            "layout_kind": "fluid_pipe_segment",
        },
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    trunk = {(int(p[0]), int(p[1])) for p in out["solver_hints"]["trunk_seed_cell_union"]}
    cleanup = {(int(p[0]), int(p[1])) for p in out["solver_hints"]["cleanup_candidate_cell_union"]}
    assert (50, 50) in cleanup
    assert (50, 50) not in trunk


def test_ela_single_cell_belt_not_in_trunk_seed() -> None:
    """Single-cell belt artifact is cleanup-only, never ``trunk_seed_cell_union`` (PR4-C)."""

    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 4, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 50, "y": 50, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    trunk = {(int(p[0]), int(p[1])) for p in out["solver_hints"]["trunk_seed_cell_union"]}
    cleanup = {(int(p[0]), int(p[1])) for p in out["solver_hints"]["cleanup_candidate_cell_union"]}
    assert (50, 50) in cleanup
    assert (50, 50) not in trunk
