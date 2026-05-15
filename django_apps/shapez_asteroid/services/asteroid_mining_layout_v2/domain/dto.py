"""
Frozen dataclass DTOs (CANON ``03_data_schema_dto.md`` §19.1, §E, §16.3).

No solver behaviour; no v1 imports.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    decoded_blueprint as _decoded_blueprint_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    existing_layout as _existing_layout_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    orchestration as _orchestration_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    placement as _placement_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    reconstruction as _recon_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    routing as _routing_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    validation as _validation_domain,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime import (
    trace_events as _runtime_trace_domain,
)

DecodedBlueprintDocument = _decoded_blueprint_domain.DecodedBlueprintDocument

DecodedExistingLayoutContext = _existing_layout_domain.DecodedExistingLayoutContext
EquipmentTransportAttachment = _existing_layout_domain.EquipmentTransportAttachment
ExistingEquipmentAnalysis = _existing_layout_domain.ExistingEquipmentAnalysis
ExistingLayoutAnalysis = _existing_layout_domain.ExistingLayoutAnalysis
ExistingLayoutIssue = _existing_layout_domain.ExistingLayoutIssue
ExistingLayoutSolverHints = _existing_layout_domain.ExistingLayoutSolverHints
ExistingTransportAnalysis = _existing_layout_domain.ExistingTransportAnalysis
TransportComponentSummary = _existing_layout_domain.TransportComponentSummary

DuplicateCoordSampleDTO = _recon_domain.DuplicateCoordSampleDTO
GridMask = _recon_domain.GridMask
MineableCellSemantic = _recon_domain.MineableCellSemantic
MineableSemanticSource = _recon_domain.MineableSemanticSource
ReconstructionDTO = _recon_domain.ReconstructionDTO
ReconstructionDiagnosisDTO = _recon_domain.ReconstructionDiagnosisDTO
ReconstructionResult = _recon_domain.ReconstructionResult

ExtensionPlacement = _placement_domain.ExtensionPlacement
ExtractorPlacement = _placement_domain.ExtractorPlacement
OutputStub = _placement_domain.OutputStub
Pass1Result = _placement_domain.Pass1Result
Pass2Result = _placement_domain.Pass2Result
PlacementBundle = _placement_domain.PlacementBundle
PlacementId = _placement_domain.PlacementId

RoutePath = _routing_domain.RoutePath
RoutingFailure = _routing_domain.RoutingFailure
RoutingResult = _routing_domain.RoutingResult
Step4RoutingResult = _routing_domain.Step4RoutingResult
TrunkLoadSummary = _routing_domain.TrunkLoadSummary

FinalValidationReport = _validation_domain.FinalValidationReport

TraceEvent = _runtime_trace_domain.TraceEvent

MetricsSnapshot = _orchestration_domain.MetricsSnapshot
RoutingStateSnapshot = _orchestration_domain.RoutingStateSnapshot
SolverRunContext = _orchestration_domain.SolverRunContext
SolverRunLimits = _orchestration_domain.SolverRunLimits
