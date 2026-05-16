"""A4 snapshot DTO serialization + event type registry."""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict

import pytest

from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.replay.event_types import (
    SNAPSHOT_EVENT_TYPES,
    assert_registered_event_type,
)
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO


def test_snapshot_event_dto_serializes_to_json_roundtrip() -> None:
    ev = SnapshotEventDTO(
        event_key="f-0",
        phase="decode",
        phase_step="load",
        event_type=et.EVENT_TYPE_DECODE_RAW_LOADED,
        title="Raw loaded",
        description="d",
        before_state_json={"a": 1},
        after_state_json={"b": 2},
        delta_json={"op": "x"},
        cell_overlay_json={"cells": []},
        focus_cells_json=[(0, 0)],
        candidate_ref="",
        bundle_ref="",
        route_ref="",
        is_decision_point=False,
        is_reversible=True,
        is_placeholder=False,
        severity="info",
        metrics_json={"m": 1},
    )
    raw = json.dumps(asdict(ev))
    back = json.loads(raw)
    assert back["event_type"] == et.EVENT_TYPE_DECODE_RAW_LOADED
    assert back["before_state_json"] == {"a": 1}
    assert back["focus_cells_json"] == [[0, 0]]


_REQUIRED_EVENT_TYPES: tuple[str, ...] = (
    "decode.raw_loaded",
    "decode.normalized",
    "reconstruction.begin",
    "reconstruction.clear_old_layout",
    "reconstruction.shell_detected",
    "reconstruction.external_flood_fill",
    "reconstruction.internal_void_detected",
    "reconstruction.interior_patch_marked",
    "reconstruction.mineable_finalized",
    "candidate.generated",
    "candidate.inserted",
    "candidate.rejected",
    "candidate.removed",
    "candidate.committed",
    "routing.probe_started",
    "routing.path_previewed",
    "routing.failed",
    "routing.committed",
    "ga.generation_started",
    "ga.individual_evaluated",
    "ga.mutation_applied",
    "ga.crossover_applied",
    "ga.selection_applied",
    "ga.best_updated",
    "validation.started",
    "validation.failed",
    "validation.passed",
)


def test_event_type_registry_contains_all_required_values() -> None:
    for s in _REQUIRED_EVENT_TYPES:
        assert s in SNAPSHOT_EVENT_TYPES


def test_invalid_event_type_rejected_by_assert_registered() -> None:
    with pytest.raises(ValueError, match="Unknown snapshot event_type"):
        assert_registered_event_type("not.a.registered.type")


def test_event_type_constants_match_string_literals() -> None:
    mod = importlib.import_module("django_apps.asteroid_lab.replay.event_types")
    for name in dir(mod):
        if not name.startswith("EVENT_TYPE_"):
            continue
        val = getattr(mod, name)
        if isinstance(val, str):
            assert val in SNAPSHOT_EVENT_TYPES
