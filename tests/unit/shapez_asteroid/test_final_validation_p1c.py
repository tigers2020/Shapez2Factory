"""P1-C: exact extractor output stub when ``r`` is present."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    validate_final_mining_layout,
)


def test_miner_with_r_requires_belt_on_output_cell_not_wrong_side() -> None:
    mining_map = [
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
        {"x": 10, "y": 11, "role": "belt", "surface": "shape"},
    ]
    r = validate_final_mining_layout(mining_map)
    assert r.missing_stub_count == 1
    assert not r.geometry_valid


def test_miner_with_r_passes_when_stub_on_shape_miner_output_cell() -> None:
    mining_map = [
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
    ]
    r = validate_final_mining_layout(mining_map)
    assert r.missing_stub_count == 0
    assert r.geometry_valid


def test_isolated_belt_counts_as_orphan_transport() -> None:
    mining_map = [{"x": 5, "y": 5, "role": "belt", "surface": "shape"}]
    r = validate_final_mining_layout(mining_map)
    assert r.transport_cell_count == 1
    assert r.orphan_transport_count == 1
    assert r.orphan_shape_belt_count == 1
    assert r.orphan_fluid_pipe_count == 0
    assert r.transport_connectivity_ok is False
    assert r.connectivity_valid is False
    assert r.geometry_valid is True


def test_validate_reports_transport_connectivity_for_routed_miner_and_belt() -> None:
    """Mixed existing belt + solver-style miner row: connectivity flags stay introspectable."""

    mining_map = [
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
            "r": 0,
        },
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
        {"x": 12, "y": 10, "role": "belt", "surface": "shape"},
    ]
    r = validate_final_mining_layout(mining_map)
    assert isinstance(r.transport_connectivity_ok, bool)
    assert r.transport_cell_count >= 1


def test_miner_without_r_increments_missing_rotation_legacy_path() -> None:
    mining_map = [
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "t": "Layout_ShapeMiner",
        },
        {"x": 11, "y": 10, "role": "belt", "surface": "shape"},
    ]
    r = validate_final_mining_layout(mining_map)
    assert r.missing_extractor_rotation_count == 1
    assert r.missing_stub_count == 0
