"""Domain layering: pure domain modules avoid I/O, UI, and aggregator cycles."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_V2_DOMAIN = (
    _REPO_ROOT
    / "django_apps"
    / "shapez_asteroid"
    / "services"
    / "asteroid_mining_layout_v2"
    / "domain"
)
_RECON = _V2_DOMAIN / "reconstruction.py"
_DECODED_BLUEPRINT = _V2_DOMAIN / "decoded_blueprint.py"
_EXISTING = _V2_DOMAIN / "existing_layout.py"
_PLACEMENT = _V2_DOMAIN / "placement.py"
_ROUTING = _V2_DOMAIN / "routing.py"
_VALIDATION = _V2_DOMAIN / "validation.py"
_ORCHESTRATION = _V2_DOMAIN / "orchestration.py"


def _django_or_forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    bad: list[str] = []
    forbidden_prefixes = (
        "django",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_reconstruction_timeline",
        "django_apps.shapez_asteroid.services.behavior_artifact_collector",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime",
        "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.replay",
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                n = alias.name
                if n == "django" or n.startswith("django."):
                    bad.append(f"{path}: import {n}")
                if any(n == p or n.startswith(p + ".") for p in forbidden_prefixes if "." in p):
                    bad.append(f"{path}: import {n}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            m = node.module
            if m == "django" or m.startswith("django."):
                bad.append(f"{path}: from {m}")
            for p in forbidden_prefixes:
                if m == p or m.startswith(p + "."):
                    bad.append(f"{path}: from {m}")
    return bad


def test_domain_reconstruction_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_RECON)
    assert not offenders, "\n".join(offenders)


def test_reconstruction_dto_single_identity_across_dto_and_reconstruction_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        reconstruction as recon_mod,
    )

    assert dto_mod.ReconstructionDTO is recon_mod.ReconstructionDTO
    assert dto_mod.ReconstructionResult is recon_mod.ReconstructionResult
    assert dto_mod.GridMask is recon_mod.GridMask
    assert dto_mod.DuplicateCoordSampleDTO is recon_mod.DuplicateCoordSampleDTO
    assert dto_mod.ReconstructionDiagnosisDTO is recon_mod.ReconstructionDiagnosisDTO


def test_domain_decoded_blueprint_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_DECODED_BLUEPRINT)
    assert not offenders, "\n".join(offenders)


def test_decoded_blueprint_dto_single_identity_across_dto_and_decoded_blueprint_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        decoded_blueprint as db_mod,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod

    assert dto_mod.DecodedBlueprintDocument is db_mod.DecodedBlueprintDocument


def test_domain_placement_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_PLACEMENT)
    assert not offenders, "\n".join(offenders)


def test_placement_dto_single_identity_across_dto_and_placement_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        placement as place_mod,
    )

    assert dto_mod.PlacementId is place_mod.PlacementId
    assert dto_mod.OutputStub is place_mod.OutputStub
    assert dto_mod.ExtractorPlacement is place_mod.ExtractorPlacement
    assert dto_mod.ExtensionPlacement is place_mod.ExtensionPlacement
    assert dto_mod.PlacementBundle is place_mod.PlacementBundle
    assert dto_mod.Pass1Result is place_mod.Pass1Result
    assert dto_mod.Pass2Result is place_mod.Pass2Result


def test_domain_existing_layout_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_EXISTING)
    assert not offenders, "\n".join(offenders)


def test_domain_routing_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_ROUTING)
    assert not offenders, "\n".join(offenders)


def test_routing_dto_single_identity_across_dto_and_routing_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        routing as route_mod,
    )

    assert dto_mod.RoutePath is route_mod.RoutePath
    assert dto_mod.RoutingFailure is route_mod.RoutingFailure
    assert dto_mod.TrunkLoadSummary is route_mod.TrunkLoadSummary
    assert dto_mod.Step4RoutingResult is route_mod.Step4RoutingResult
    assert dto_mod.RoutingResult is route_mod.RoutingResult


def test_domain_validation_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_VALIDATION)
    assert not offenders, "\n".join(offenders)


def test_validation_dto_single_identity_across_dto_and_validation_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        validation as val_mod,
    )

    assert dto_mod.FinalValidationReport is val_mod.FinalValidationReport


def test_domain_orchestration_module_has_no_django_or_output_stack_imports() -> None:
    offenders = _django_or_forbidden_imports(_ORCHESTRATION)
    assert not offenders, "\n".join(offenders)


def test_orchestration_dto_single_identity_across_dto_and_orchestration_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        orchestration as orch_mod,
    )

    assert dto_mod.SolverRunLimits is orch_mod.SolverRunLimits
    assert dto_mod.RoutingStateSnapshot is orch_mod.RoutingStateSnapshot
    assert dto_mod.MetricsSnapshot is orch_mod.MetricsSnapshot
    assert dto_mod.SolverRunContext is orch_mod.SolverRunContext


def test_existing_layout_dto_single_identity_across_dto_and_existing_layout_modules() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import dto as dto_mod
    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
        existing_layout as el_mod,
    )

    assert dto_mod.ExistingLayoutAnalysis is el_mod.ExistingLayoutAnalysis
    assert dto_mod.DecodedExistingLayoutContext is el_mod.DecodedExistingLayoutContext
    assert dto_mod.TransportComponentSummary is el_mod.TransportComponentSummary
    assert dto_mod.ExistingTransportAnalysis is el_mod.ExistingTransportAnalysis
    assert dto_mod.EquipmentTransportAttachment is el_mod.EquipmentTransportAttachment
    assert dto_mod.ExistingEquipmentAnalysis is el_mod.ExistingEquipmentAnalysis
    assert dto_mod.ExistingLayoutIssue is el_mod.ExistingLayoutIssue
    assert dto_mod.ExistingLayoutSolverHints is el_mod.ExistingLayoutSolverHints
