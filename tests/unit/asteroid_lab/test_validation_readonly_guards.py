"""Track D+ PR-2 — catalog validation read-only import and immutability guards."""

from __future__ import annotations

import ast
from pathlib import Path

from django_apps.asteroid_lab.adapters.catalog_placement_validation import (
    validate_catalog_placements,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingFootprintCell,
    TransportRegistryEntry,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import (
    build_pattern_library,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.validation import catalog_layout_validation

_REPO_ROOT = Path(__file__).resolve().parents[3]
_VALIDATION_MODULE = (
    _REPO_ROOT / "django_apps/asteroid_lab/adapters/catalog_placement_validation.py"
)
_AUDIT_MODULE = _REPO_ROOT / "django_apps/asteroid_lab/adapters/catalog_placement_audit.py"
_LAYOUT_VALIDATION_MODULE = (
    _REPO_ROOT
    / "django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py"
)

_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization.routing.route_probe",
    "django_apps.asteroid_lab.optimization.commit.incremental_commit",
    "django_apps.asteroid_lab.optimization.commit",
    "django_apps.asteroid_lab.optimization.candidates.candidate_generator",
)

_GUARDED_MODULES = (
    _VALIDATION_MODULE,
    _AUDIT_MODULE,
    _LAYOUT_VALIDATION_MODULE,
)


def _forbidden_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    issues: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module = alias.name
                for prefix in _FORBIDDEN_IMPORT_PREFIXES:
                    if module == prefix or module.startswith(prefix + "."):
                        issues.append(f"{path.name}: imports {module}")
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        for prefix in _FORBIDDEN_IMPORT_PREFIXES:
            if node.module == prefix or node.module.startswith(prefix + "."):
                issues.append(f"{path.name}: imports {node.module}")
    return issues


def test_catalog_validation_modules_do_not_import_probe_or_commit() -> None:
    violations: list[str] = []
    for module_path in _GUARDED_MODULES:
        violations.extend(_forbidden_imports(module_path))
    assert violations == []


def _catalog_slice() -> BuildingCatalogSlice:
    canonical_id = "bv:1"
    footprint = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    )
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", canonical_id),),
        variants=(VariantIdentity(canonical_id, "miner_a"),),
        variant_geometries=(
            VariantGeometryCatalog(
                canonical_id=canonical_id,
                internal_name="miner_a",
                footprint_cells=footprint,
                connectors=(),
            ),
        ),
    )


def _candidate(
    *,
    occupied: frozenset[tuple[int, int]],
    ref: CatalogPlacementRef | None = None,
) -> BundleCandidate:
    pat = build_pattern_library()[0]
    return BundleCandidate(
        candidate_id="c1",
        anchor_coord=(5, 7),
        pattern=pat,
        occupied_cells=occupied,
        output_stub=(9, 7),
        output_dir="E",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=ref,
    )


def test_validate_catalog_placements_does_not_mutate_candidate() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    occupied = frozenset({(5, 7), (6, 7)})
    cand = _candidate(occupied=occupied, ref=ref)
    before_cells = cand.occupied_cells
    before_ref = cand.catalog_placement_ref
    validate_catalog_placements(("c1",), {"c1": cand}, sl)
    assert cand.occupied_cells == before_cells
    assert cand.catalog_placement_ref == before_ref


def test_catalog_layout_validation_does_not_import_probe_route_symbol() -> None:
    assert not hasattr(catalog_layout_validation, "probe_route")
