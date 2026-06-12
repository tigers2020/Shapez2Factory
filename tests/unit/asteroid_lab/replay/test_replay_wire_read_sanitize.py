"""Replay wire read sanitizer contract (Slice 1)."""

from __future__ import annotations

import copy

import pytest

from django_apps.asteroid_lab.replay.effective_cell_view import merge_effective_cell_view
from django_apps.asteroid_lab.replay.replay_cell_index import cell_key
from django_apps.asteroid_lab.replay.replay_wire_read_sanitize import (
    ReplayWireAuditError,
    audit_replay_wire_cell,
    is_candidate_output_hint_kind,
    sanitize_replay_wire_cell_for_read,
)

_LEGACY_CANDIDATE_ROW = {
    "x": 10,
    "y": 7,
    "kind": "candidate_miner",
    "transport": "shape_belt",
    "rotation": 0,
    "layer": 0,
}

_CANONICAL_CANDIDATE_ROW = {
    "x": 10,
    "y": 7,
    "kind": "candidate_miner",
    "transport": "none",
    "transport_kind": "none",
    "output_transport_kind": "space_belt",
    "rotation": 0,
    "layer": 0,
}


def test_stable_view_index_key_default_layer() -> None:
    assert cell_key(10, 7) == "10,7"
    assert cell_key(10, 7, 0) == "10,7"


def test_stable_view_index_key_nonzero_layer() -> None:
    assert cell_key(10, 7, 2) == "2:10,7"


def test_is_candidate_output_hint_kind() -> None:
    assert is_candidate_output_hint_kind("candidate_miner")
    assert not is_candidate_output_hint_kind("space_belt")


def test_sanitizer_compat_legacy_transport() -> None:
    out = sanitize_replay_wire_cell_for_read(copy.deepcopy(_LEGACY_CANDIDATE_ROW))
    assert out["transport"] == "none"
    assert out["transport_kind"] == "none"
    assert out["output_transport_kind"] == "space_belt"


def test_sanitizer_merge_parity_with_canonical_wire() -> None:
    legacy = sanitize_replay_wire_cell_for_read(copy.deepcopy(_LEGACY_CANDIDATE_ROW))
    canonical = copy.deepcopy(_CANONICAL_CANDIDATE_ROW)
    legacy_view = merge_effective_cell_view(
        x=10,
        y=7,
        full_cell={"x": 10, "y": 7, "kind": "asteroid_shape_field", "transport": "none"},
        overlay_cells=[legacy],
    )
    canonical_view = merge_effective_cell_view(
        x=10,
        y=7,
        full_cell={"x": 10, "y": 7, "kind": "asteroid_shape_field", "transport": "none"},
        overlay_cells=[canonical],
    )
    assert legacy_view is not None and canonical_view is not None
    assert legacy_view.output_transport_kind == canonical_view.output_transport_kind == "space_belt"
    assert legacy_view.occupant_kind == canonical_view.occupant_kind


def test_sanitizer_does_not_normalize_committed_transport() -> None:
    committed = {
        "x": 3,
        "y": 4,
        "kind": "space_belt",
        "transport": "shape_belt",
        "tile_type": "SpaceBelt_Forward",
    }
    with pytest.raises(ReplayWireAuditError):
        audit_replay_wire_cell(committed)
    unchanged = sanitize_replay_wire_cell_for_read(copy.deepcopy(committed))
    assert unchanged["transport"] == "shape_belt"
