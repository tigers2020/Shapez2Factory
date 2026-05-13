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
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.step4_failure_types import (
    Step4FailureClassificationWire,
    Step4RoutingFailureDetailWire,
    Step4SearchStatsWire,
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
    "IssueSeverity",
    "MiningLayoutGridRollback",
    "MiningMapCell",
    "MiningMapCellsByCoord",
    "MiningMapRole",
    "MiningMapRows",
    "MutableMiningMapCell",
    "Pass2GoalTraceWire",
    "Pass2RouteProbeStatsWire",
    "SourceKindWire",
    "Step4FailureClassificationWire",
    "Step4RoutingFailureDetailWire",
    "Step4SearchStatsWire",
    "SolverTimelineFrame",
    "SolverTimelinePass3Payload",
]
