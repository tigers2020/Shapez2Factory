"""P4: Reclaim shadow scan, bounded reclaim loop (§12.6), provisional + incremental route commit.

See ``documents/Algorithm/mining_solver_cursor_sessions/10_step6_reclaim_loop.md`` §12.2–12.6.

Implementation is split under ``reclaim_*.py``; this module re-exports the stable public surface.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    ReclaimShadowScanResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD,
    MAX_RECLAIM_INCREMENTAL_ROUTE_LENGTH_RATIO,
    MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO,
    MAX_RECLAIM_ITERATIONS,
    MAX_RECLAIM_SHADOW_SCAN_LIMIT,
    MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS,
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
    P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL,
    P4_RECLAIM_INCREMENTAL_ROUTE_PLACEMENT_ID,
    P4_RECLAIM_PROVISIONAL_PLACEMENT_ID,
    P4_REJECT_FINAL_ROUTE_OVERLAP,
    P4_REJECT_GAIN_RATIO,
    P4_REJECT_HARD_PROTECTED_CORRIDOR,
    P4_REJECT_INCREMENTAL_ROUTE_LENGTH_RATIO,
    P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
    P4_REJECT_NO_INCREMENTAL_ROUTE,
    P4_REJECT_NO_OUTPUT_STUB,
    P4_REJECT_NO_SHADOW_CANDIDATE,
    P4_REJECT_SOFT_PROTECTED_CORRIDOR,
    P4_REJECT_VALIDATION,
    P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED,
    P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE,
    P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE,
    P4_SOFT_REPLACE_REJECT_NO_ROUTING_JOB,
    P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED,
    P4_SOFT_REPLACE_REJECT_OLD_NOT_TRANSPORT,
    P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED,
    P4_SOFT_REPLACE_REJECT_VALIDATION,
    P4_SOFT_REPLACE_ROUTE_PLACEMENT_ID,
    P4_SOFT_REPLACE_V1_CONTRACT,
    P4_SOFT_REPLACE_V2_CONTRACT,
    RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    placement_stub_route_probe_path,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    protected_corridors_for_reclaim,
    protected_corridors_read_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridors import (
    solver_routing_state_for_p4_reclaim as solver_routing_state_for_p4_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _all_transport_cells,
    _mineable_cur_for_reclaim,
    _reclaimed_interior_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_p4_bundle import (
    _p4_bundle_eval,
    _p4_selected_candidate_rank,
    select_best_accepted_p4_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_route_metrics import (  # noqa: E501
    _path_additional_route_cost,
    _path_additional_route_cost_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_commit import (  # noqa: E501
    p4_reclaim_provisional_commit_neutral_trace,
    p4_reclaim_shadow_placeholder,
    run_p4_reclaim_loop_after_pass3,
    run_p4_reclaim_provisional_commit_after_pass3,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan import (  # noqa: E501
    _evaluate_one_shadow_bundle,
    reclaim_shadow_scan_core_after_pass3,
    run_reclaim_shadow_scan_after_pass3,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_soft_replace import (  # noqa: E501
    _try_atomic_replace_soft_corridor,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    mineable_and_asteroid_coords as _mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    validate_final_mining_layout,
)

__all__ = [
    "_path_additional_route_cost",
    "_path_additional_route_cost_detail",
    "DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD",
    "MAX_RECLAIM_INCREMENTAL_ROUTE_LENGTH_RATIO",
    "MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO",
    "MAX_RECLAIM_ITERATIONS",
    "MAX_RECLAIM_SHADOW_SCAN_LIMIT",
    "MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS",
    "P4_RECLAIM_CORRIDOR_SOURCE_EMPTY",
    "P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL",
    "P4_RECLAIM_INCREMENTAL_ROUTE_PLACEMENT_ID",
    "P4_RECLAIM_PROVISIONAL_PLACEMENT_ID",
    "P4_REJECT_FINAL_ROUTE_OVERLAP",
    "P4_REJECT_GAIN_RATIO",
    "P4_REJECT_HARD_PROTECTED_CORRIDOR",
    "P4_REJECT_INCREMENTAL_ROUTE_LENGTH_RATIO",
    "P4_REJECT_INTERNAL_TRANSPORT_BUDGET",
    "P4_REJECT_NO_INCREMENTAL_ROUTE",
    "P4_REJECT_NO_OUTPUT_STUB",
    "P4_REJECT_NO_SHADOW_CANDIDATE",
    "P4_REJECT_SOFT_PROTECTED_CORRIDOR",
    "P4_REJECT_VALIDATION",
    "P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED",
    "P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE",
    "P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE",
    "P4_SOFT_REPLACE_REJECT_NO_ROUTING_JOB",
    "P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED",
    "P4_SOFT_REPLACE_REJECT_OLD_NOT_TRANSPORT",
    "P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED",
    "P4_SOFT_REPLACE_REJECT_VALIDATION",
    "P4_SOFT_REPLACE_ROUTE_PLACEMENT_ID",
    "P4_SOFT_REPLACE_V1_CONTRACT",
    "P4_SOFT_REPLACE_V2_CONTRACT",
    "RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS",
    "ReclaimShadowScanResult",
    "placement_stub_route_probe_path",
    "_all_transport_cells",
    "_evaluate_one_shadow_bundle",
    "_mineable_and_asteroid_coords",
    "_mineable_cur_for_reclaim",
    "_p4_bundle_eval",
    "_p4_selected_candidate_rank",
    "_reclaimed_interior_transport_cells",
    "_try_atomic_replace_soft_corridor",
    "p4_reclaim_provisional_commit_neutral_trace",
    "p4_reclaim_shadow_placeholder",
    "protected_corridors_for_reclaim",
    "protected_corridors_read_for_reclaim",
    "reclaim_shadow_scan_core_after_pass3",
    "run_p4_reclaim_loop_after_pass3",
    "run_p4_reclaim_provisional_commit_after_pass3",
    "run_reclaim_shadow_scan_after_pass3",
    "select_best_accepted_p4_bundle",
    "solver_routing_state_for_p4_reclaim",
    "validate_final_mining_layout",
]
