"""Layout-solver DTO helpers: stable contracts without import side effects.

Algorithm code stays in sibling modules; this subpackage holds shared literals
and (future) typed shapes that must not pull in orchestration.
"""

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.existing_layout_types import (
    CoordWire,
    ExistingEquipmentAnalysisWire,
    ExistingLayoutAnalysisWire,
    ExistingLayoutBBoxWire,
    ExistingLayoutIssueWire,
    ExistingLayoutSolverHintsWire,
    ExistingTransportAnalysisWire,
    ExistingTransportComponentWire,
    IssueSeverity,
    SourceKindWire,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.mining_map_cell import (
    MiningMapCell,
    MiningMapCellsByCoord,
    MiningMapRole,
    MiningMapRows,
    MutableMiningMapCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.pass12_probe_types import (
    Pass2GoalTraceWire,
    Pass2RouteProbeStatsWire,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.recovery_semantics import (
    COMMIT_REASON_VALUES,
    INVALID_COMMIT_REASON_VALUES,
    RECOVERY_TRIGGER_VALUES,
    CommitReason,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    is_commit_reason,
    is_invalid_commit_reason,
    is_recovery_trigger,
    normalize_success_commit_reason,
    promote_misfiled_rejected_reason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.step4_failure_types import (
    Step4FailureClassificationWire,
    Step4RoutingFailureDetailWire,
    Step4RoutingFailureRowWire,
    Step4SearchStatsWire,
    step4_routing_failure_row_to_public_dict,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.timeline_types import (
    MiningLayoutGridRollback,
    SolverTimelineFrame,
    SolverTimelinePass3Payload,
)

__all__ = [
    "CoordWire",
    "ExistingEquipmentAnalysisWire",
    "ExistingLayoutAnalysisWire",
    "ExistingLayoutBBoxWire",
    "ExistingLayoutIssueWire",
    "ExistingLayoutSolverHintsWire",
    "ExistingTransportAnalysisWire",
    "ExistingTransportComponentWire",
    "COMMIT_REASON_VALUES",
    "CommitReason",
    "INVALID_COMMIT_REASON_VALUES",
    "IssueSeverity",
    "MiningLayoutGridRollback",
    "MiningMapCell",
    "MiningMapCellsByCoord",
    "MiningMapRole",
    "MiningMapRows",
    "MutableMiningMapCell",
    "Pass2GoalTraceWire",
    "Pass2RouteProbeStatsWire",
    "RECOVERY_TRIGGER_VALUES",
    "RecoveryTrigger",
    "RejectedReason",
    "RollbackReason",
    "SourceKindWire",
    "Step4FailureClassificationWire",
    "Step4RoutingFailureDetailWire",
    "Step4RoutingFailureRowWire",
    "Step4SearchStatsWire",
    "is_commit_reason",
    "is_invalid_commit_reason",
    "is_recovery_trigger",
    "normalize_success_commit_reason",
    "promote_misfiled_rejected_reason",
    "SolverTimelineFrame",
    "SolverTimelinePass3Payload",
    "step4_routing_failure_row_to_public_dict",
]
