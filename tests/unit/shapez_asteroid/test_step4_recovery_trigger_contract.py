"""D2-B1: STEP4 recovery_trigger contract vs Algorithm §4.3 (no retry loop)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    placement_record_to_failure_dict,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver import (
    recovery_return_policy as rrp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as s4_merge,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_recovery_trigger as s4_recov,
)


def _one_mineable_cell_map() -> list[dict[str, object]]:
    return [{"role": "mineable", "x": 0, "y": 0, "kind": "blue", "rotation": 0}]


def test_step4_primary_trigger_none_on_clean_skip() -> None:
    r = s4_merge.step4_routing_skipped_result(_one_mineable_cell_map())
    assert s4_recov.step4_primary_recovery_trigger_from_result(r) is None


def test_step4_primary_trigger_routing_on_incomplete() -> None:
    r = s4_merge.step4_routing_skipped_result(_one_mineable_cell_map())
    r = replace(r, committed=False, complete_routing_success=False)
    assert (
        s4_recov.step4_primary_recovery_trigger_from_result(r)
        == RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    )


def test_step4_primary_trigger_capacity_from_trunk_signal() -> None:
    r = s4_merge.step4_routing_skipped_result(_one_mineable_cell_map())
    tl = dict(r.trunk_load)
    tl[s4_recov.STEP4_TRUNK_LOAD_CAPACITY_FAILURE_SIGNAL_KEY] = True
    r = replace(r, trunk_load=tl)
    assert (
        s4_recov.step4_primary_recovery_trigger_from_result(r)
        == RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE
    )


def test_step4_primary_trigger_capacity_from_failure_row() -> None:
    r = s4_merge.step4_routing_skipped_result(_one_mineable_cell_map())
    r = replace(
        r,
        committed=True,
        complete_routing_success=True,
        routing_failures=(
            {
                "recovery_trigger": RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
                "reason": "synthetic_capacity_fixture",
            },
        ),
    )
    assert (
        s4_recov.step4_primary_recovery_trigger_from_result(r)
        == RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE
    )


def test_step4_triggers_map_to_recovery_return_policy() -> None:
    r_pol = rrp.recovery_return_policy_for_trigger(RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE)
    assert r_pol.policy_id == rrp.RecoveryReturnPolicyId.STEP4_RETRY_ROLLBACK_ALTERNATE_TRUNK
    c_pol = rrp.recovery_return_policy_for_trigger(RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE)
    assert c_pol.policy_id == rrp.RecoveryReturnPolicyId.STEP4_RETRY_TRUNK_SPLIT_OFFENDING_ROLLBACK
    assert r_pol.reenters_step4 and c_pol.reenters_step4


def test_placement_failure_dict_uses_recovery_trigger_not_commit_reason() -> None:
    rec = PlacementCommitRecord(
        placement_id="p1-000001",
        placement_pass="pass1",
        extractor_cell=(0, 0),
        extension_cells=(),
        stub_cell=(1, 0),
        transport_kind="shape",
        state=PlacementCommitState.QUARANTINED_UNROUTED,
    )
    d = placement_record_to_failure_dict(rec, reason="no_route")
    assert "commit_reason" not in d
    assert d["recovery_trigger"] == RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
