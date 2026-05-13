"""Failing regression contracts: runtime authority must not come from trace/replay mirrors.

Canon: ``documents/Algorithm/mining_solver_cursor_sessions/`` 08 (STEP4), 12 (corridors), 14 (replay).

These tests encode stricter authority than current code: when ``routing_state`` is absent,
**all** reclaim-side corridor-related runtime surfaces must stay empty (no synthesis from
``pass3_trace``, replay-shaped rows, or STEP 0.5 hints). Patches are intentionally deferred.
"""

from __future__ import annotations

import ast
from pathlib import Path

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import constants
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
    ROLLUP_COMMIT_REASONS_CANONICAL,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_for_reclaim,
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.recovery_policy import (
    synthesize_recovery_validation_outcome,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.semantic_contracts import (
    partition_pass3_commit_reason_payload,
)


def _assert_empty_hard_soft_source_empty(result: object) -> None:
    assert result.hard == frozenset()
    assert result.soft == frozenset()
    assert result.source == P4_RECLAIM_CORRIDOR_SOURCE_EMPTY


# --- (1) protected_corridors_for_reclaim must not synthesize hard/soft from pass3_trace ---


def test_protected_corridors_for_reclaim_no_routing_state_trace_must_not_synthesize_hard_soft() -> (
    None
):
    pcs = protected_corridors_for_reclaim(
        pass3_trace={
            "protected_corridors": {"hard": [[9, 1]], "soft": [[8, 2]]},
            "p3e3_guarded_commit_candidate": {
                "touched_hard_protected_cells": [[7, 3]],
                "touched_soft_protected_cells": [[6, 4]],
            },
        },
        solver_routing_state=None,
    )
    _assert_empty_hard_soft_source_empty(pcs)


# --- (1b) When routing_state is absent, no *runtime* corridor attachment from hints either ---


def test_protected_corridors_for_reclaim_no_routing_state_existing_layout_hints_must_not_attach() -> (
    None
):
    pcs = protected_corridors_for_reclaim(
        pass3_trace={},
        solver_routing_state=None,
        existing_layout_solver_hints={
            "trunk_seed_cell_union": [[4, 4]],
            "cleanup_candidate_cell_union": [[3, 3]],
        },
    )
    _assert_empty_hard_soft_source_empty(pcs)
    assert pcs.existing_layout_hints_cells == frozenset()


# --- (2) trace_event-shaped pass3_trace must not populate *any* reclaim runtime corridor cells ---


def test_trace_event_shape_pass3_trace_must_not_reconstruct_runtime_corridor_authority() -> None:
    """§14: replay/trace wire must not back-fill hard/soft/probe/candidate when pool is empty."""

    pc = protected_corridors_read_for_reclaim(
        pass3_trace={
            "event_type": "trace_event",
            "phase": "pass3",
            "protected_corridors": {"hard": [[11, 2]], "soft": [[12, 2]]},
            "corridor_probe_candidate_cells": [[13, 3]],
            "corridor_probe_discarded_cells": [[14, 4]],
            "layout_snapshot_before_pass3": {"marker": "replay_only"},
            "computation_cycle": 10,
        },
        solver_routing_state=None,
    )
    _assert_empty_hard_soft_source_empty(pc)
    assert pc.probe_candidate_cells == frozenset()
    assert pc.probe_discarded_cells == frozenset()
    assert pc.candidate == frozenset()


# --- (3) trunk_load["step4_committed"] must not be read for Pass3 / reclaim inference ---


def _mining_layout_service_root() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "django_apps"
        / "shapez_asteroid"
        / "services"
        / "asteroid_mining_layout"
    )


def test_trunk_load_step4_committed_not_read_for_runtime_inference() -> None:
    """08 §9.6: gate uses explicit ``Step4RoutingResult.committed`` — never trunk_load mirror key."""

    root = _mining_layout_service_root()
    offenders: list[str] = []
    allow_write = frozenset(
        {
            "step4_merge_routing.py",
            "step4_trunk_load.py",
        }
    )
    for path in sorted(root.rglob("*.py")):
        if path.name in allow_write:
            continue
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if "step4_committed" not in line:
                continue
            if "trunk_load" not in line:
                continue
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            offenders.append(f"{path.relative_to(root)}:{lineno}:{stripped}")
    assert not offenders, "trunk_load + step4_committed on same line (possible mirror inference):\n" + "\n".join(
        offenders[:25]
    )


# --- (4) recovery_trigger must not populate commit_reason (rollup contract) ---


def test_recovery_trigger_literals_disjoint_from_rollup_commit_reasons() -> None:
    """§13.5: recovery_trigger vocabulary must never be a canonical success commit_reason."""

    triggers = {
        v
        for k, v in vars(constants).items()
        if k.startswith("RECOVERY_TRIGGER_") and isinstance(v, str)
    }
    assert triggers.isdisjoint(ROLLUP_COMMIT_REASONS_CANONICAL), triggers & ROLLUP_COMMIT_REASONS_CANONICAL


def test_synthesize_recovery_validation_outcome_does_not_copy_recovery_trigger_to_commit_reason() -> (
    None
):
    summary = {
        "return_reason": "ok",
        "recovery_trigger": constants.RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
        "pass3_commit_reason": constants.RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
        "pass3_committed": True,
        "pass3_final_committed": True,
    }
    synthesize_recovery_validation_outcome(summary)
    out = summary["recovery_validation_outcome"]
    assert out["recovery_trigger"] == constants.RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    assert out["commit_reason"] is None


# --- (5) committed=false ⇒ commit_reason slot stays null at partition boundary ---


def test_partition_pass3_commit_reason_uncommitted_implies_no_commit_reason_even_if_raw_string() -> (
    None
):
    cr, promoted = partition_pass3_commit_reason_payload(
        constants.P3F_COMMIT_REASON_NORMAL_GAIN,
        pass3_committed=False,
        pass3_final_committed=True,
    )
    assert cr is None
    assert promoted is None


# --- (6) replay-only keys must not alter reclaim corridor read when routing_state absent ---


def test_replay_only_snapshot_keys_do_not_fill_protected_corridor_runtime_fields() -> None:
    pc = protected_corridors_read_for_reclaim(
        pass3_trace={
            "layout_snapshot_before_pass3": {"fake": "replay"},
            "layout_snapshot_after_pass3": {"fake": "replay"},
            "layout_snapshot_phase": "pass3",
        },
        solver_routing_state=None,
    )
    _assert_empty_hard_soft_source_empty(pc)
    assert pc.probe_candidate_cells == frozenset()
    assert pc.probe_discarded_cells == frozenset()
    assert pc.candidate == frozenset()


# --- (6b) recovery branch selection must not depend on replay_events list (import guard) ---


def test_recovery_orchestrator_does_not_iterate_replay_events_for_policy() -> None:
    path = _mining_layout_service_root() / "solver_pipeline" / "recovery_orchestrator.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    bad = False
    for node in ast.walk(tree):
        if isinstance(node, ast.For) and isinstance(node.iter, ast.Name):
            if node.iter.id == "replay_events":
                bad = True
                break
        if isinstance(node, ast.comprehension) and isinstance(node.iter, ast.Name):
            if node.iter.id == "replay_events":
                bad = True
                break
    assert not bad, "recovery_orchestrator must not loop replay_events for branching policy"


# --- (6c) corridor classification: no trunk_load merge into reclaim merge helper ---


def test_merge_step4_corridor_routing_mapping_docstring_forbids_trunk_load_authority() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim import (
        reclaim_corridors as rc,
    )

    doc = (rc.merge_step4_corridor_routing_mapping.__doc__ or "").lower()
    assert "never" in doc or "output" in doc or "mirror" in doc
    assert "trunk_load" in doc


def test_merge_step4_corridor_routing_mapping_ignores_trunk_load_protected_corridors_payload() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
        merge_step4_corridor_routing_mapping,
    )

    merged = merge_step4_corridor_routing_mapping(
        routing_state=None,
        trunk_load={
            "protected_corridors": {"hard": [[1, 1]], "soft": [[2, 2]]},
            "hard_protected_corridors": [[3, 3]],
            "step4_committed": True,
        },
    )
    assert merged is None
