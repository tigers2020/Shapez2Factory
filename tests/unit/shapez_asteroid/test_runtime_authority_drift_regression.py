"""Regression gates for runtime authority drift.

These tests intentionally encode the future contract and fail against the current drift:
runtime protected-corridor authority must come from STEP4 ``routing_state`` only.
"""

from __future__ import annotations

from types import SimpleNamespace

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow import (
    protected_corridors_for_reclaim,
    protected_corridors_read_for_reclaim,
    solver_routing_state_for_p4_reclaim,
)


def _assert_empty_runtime_authority(result: object) -> None:
    assert result.hard == frozenset()
    assert result.soft == frozenset()
    assert result.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY


def test_pass3_trace_hard_corridor_fallback_is_not_runtime_authority() -> None:
    result = protected_corridors_for_reclaim(
        pass3_trace={"protected_corridors": {"hard": [[4, 1]], "soft": []}},
        solver_routing_state=None,
    )

    _assert_empty_runtime_authority(result)


def test_pass3_trace_soft_corridor_fallback_is_not_runtime_authority() -> None:
    result = protected_corridors_for_reclaim(
        pass3_trace={"protected_corridors": {"hard": [], "soft": [[5, 2]]}},
        solver_routing_state=None,
    )

    _assert_empty_runtime_authority(result)


def test_pass3_trace_mixed_authority_source_is_not_runtime_authority() -> None:
    result = protected_corridors_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": [[4, 1]], "soft": [[5, 2]]},
            "p3e3_guarded_commit_candidate": {
                "touched_hard_protected_cells": [[9, 1]],
                "touched_soft_protected_cells": [[10, 2]],
            },
        },
        solver_routing_state=None,
    )

    _assert_empty_runtime_authority(result)


def test_trace_event_protected_corridors_never_reconstruct_runtime_state() -> None:
    result = protected_corridors_read_for_reclaim(
        pass3_trace={
            "event_type": "trace_event",
            "phase": "pass3",
            "protected_corridors": {"hard": [[11, 2]], "soft": [[12, 2]]},
        },
        solver_routing_state=None,
    )

    _assert_empty_runtime_authority(result)


def test_trunk_load_mirrors_do_not_become_authority_without_routing_state() -> None:
    step4_result = SimpleNamespace(
        routing_state=None,
        trunk_load={
            "protected_corridors": {"hard": [[1, 1]], "soft": [[2, 2]]},
            "hard_protected_corridors": [[3, 3]],
            "soft_protected_corridors": [[4, 4]],
        },
    )

    merged = solver_routing_state_for_p4_reclaim(step4_result)
    result = protected_corridors_for_reclaim(pass3_trace={}, solver_routing_state=merged)

    assert merged is None
    _assert_empty_runtime_authority(result)


def test_trunk_load_mirrors_do_not_fill_empty_routing_state_corridors() -> None:
    step4_result = SimpleNamespace(
        routing_state={
            "source": "step4_committed_routes",
            "protected_corridors": {"hard": [], "soft": []},
            "hard_protected_corridors": [],
            "soft_protected_corridors": [],
        },
        trunk_load={
            "protected_corridors": {"hard": [[1, 1]], "soft": [[2, 2]]},
            "hard_protected_corridors": [[3, 3]],
            "soft_protected_corridors": [[4, 4]],
        },
    )

    merged = solver_routing_state_for_p4_reclaim(step4_result)
    result = protected_corridors_for_reclaim(pass3_trace={}, solver_routing_state=merged)

    assert merged == step4_result.routing_state
    _assert_empty_runtime_authority(result)


def test_replay_only_degraded_trace_fields_do_not_affect_runtime_authority() -> None:
    result = protected_corridors_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": "degraded-replay-field", "soft": [[7, 7]]},
            "corridor_probe_candidate_cells": [[8, 8]],
            "corridor_probe_discarded_cells": [[9, 9]],
        },
        solver_routing_state=None,
    )

    _assert_empty_runtime_authority(result)


def test_p3e3_touched_replay_fields_do_not_affect_runtime_authority() -> None:
    result = protected_corridors_for_reclaim(
        pass3_trace={
            "p3e3_guarded_commit_candidate": {
                "touched_hard_protected_cells": [[13, 2]],
                "touched_soft_protected_cells": [[14, 2]],
            },
        },
        solver_routing_state=None,
    )

    _assert_empty_runtime_authority(result)
