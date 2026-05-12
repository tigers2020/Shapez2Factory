"""STEP4 recovery trigger classification (Algorithm §4.3 / D2-B1).

Classification uses only :class:`Step4RoutingResult` fields set during STEP4 merge — not
``commit_reason``, not replay/NDJSON, not ``solver_summary`` consumption.

Capacity vs routing: emit ``step4_capacity_failure`` only when an explicit discriminator is
present (failure-row ``recovery_trigger`` or trunk ``step4_capacity_failure_signal``).
Until STEP4 implements capacity failure, the signal key is **reserved** and never written
by merge (see ``documents/refactory/algorithm_deviation_deletion_audit`` D2-B1 / D2-B2).
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE,
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4RoutingResult,
)

# Trunk-load key reserved for future §4.3 capacity discriminator (bool).
# Merge does not set it in B1.
STEP4_TRUNK_LOAD_CAPACITY_FAILURE_SIGNAL_KEY = "step4_capacity_failure_signal"

__all__ = [
    "STEP4_TRUNK_LOAD_CAPACITY_FAILURE_SIGNAL_KEY",
    "step4_primary_recovery_trigger_from_result",
]


def step4_primary_recovery_trigger_from_result(result: Step4RoutingResult) -> str | None:
    """Return canonical §4.3 recovery trigger for STEP4, or ``None`` if no failure class."""

    tl = result.trunk_load
    if bool(tl.get(STEP4_TRUNK_LOAD_CAPACITY_FAILURE_SIGNAL_KEY)):
        return RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE
    for row in result.routing_failures:
        if row.get("recovery_trigger") == RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE:
            return RECOVERY_TRIGGER_STEP4_CAPACITY_FAILURE

    if not result.committed or not result.complete_routing_success:
        return RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    if result.routing_failures:
        return RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    if result.rolled_back_placement_ids or result.quarantined_placement_ids:
        return RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    return None
