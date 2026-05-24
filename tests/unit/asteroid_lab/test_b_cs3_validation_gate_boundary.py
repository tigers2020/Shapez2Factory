"""B-CS3 — validation gate boundary audit (Axis B).

Spec: docs/superpowers/specs/2026-05-24-b-cs3-validation-gate-audit-design.md
PASS authority: AST import guards, immutability deepcopy, call sentinels, pipeline ordering.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

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
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    validate_pipeline_layout,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PIPELINE_PATH = _REPO_ROOT / "django_apps/asteroid_lab/optimization/pipeline.py"

_VALIDATION_MODULE_PATHS = (
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/validation/final_validation.py",
    _REPO_ROOT / "django_apps/asteroid_lab/optimization/validation/catalog_layout_validation.py",
    _REPO_ROOT / "django_apps/asteroid_lab/adapters/catalog_placement_validation.py",
    _REPO_ROOT / "django_apps/asteroid_lab/adapters/catalog_placement_audit.py",
)

_FORBIDDEN_IMPORT_PREFIXES = (
    "django_apps.asteroid_lab.optimization.routing.route_probe",
    "django_apps.asteroid_lab.optimization.commit.local_lns",
    "django_apps.asteroid_lab.optimization.commit.incremental_commit",
    "django_apps.asteroid_lab.optimization.commit",
    "django_apps.asteroid_lab.optimization.candidates.candidate_generator",
    "django_apps.asteroid_lab.optimization.routing.route_domain",
    "django_apps.asteroid_lab.services.replay_pipeline_service",
    "django_apps.asteroid_lab.services.replay_recorder",
    "django_apps.asteroid_lab.services.lab_rttp_snapshot_compose",
    "django_apps.asteroid_lab.optimization.replay_sink",
    "django_apps.asteroid_lab.replay",
    "django_apps.asteroid_lab.models",
)


class ValidationBoundaryViolation(AssertionError):
    """Raised when validation invokes a forbidden repair/route/replay API."""


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
    occupied: frozenset[Coord],
    reachable: bool = True,
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
        reachable=reachable,
        catalog_placement_ref=ref,
    )


def _minimal_inp(
    *,
    mineable: frozenset[Coord] | None = None,
    catalog_slice: BuildingCatalogSlice | None = None,
) -> OptimizationInput:
    cells = mineable or frozenset({(5, 7), (6, 7), (9, 7)})
    return OptimizationInput(
        mineable_cells=cells,
        rim_cells=frozenset(),
        inner_cells=cells,
        external_void_cells=frozenset(),
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=(),
        existing_transport_cells=frozenset(),
        catalog_slice=catalog_slice,
    )


def _valid_layout_fixtures() -> tuple[
    tuple[str, ...],
    frozenset[Coord],
    dict[str, BundleCandidate],
    OptimizationInput,
]:
    sl = _catalog_slice()
    occupied = frozenset({(5, 7), (6, 7)})
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=occupied, ref=ref)
    reserved = frozenset({(9, 7)})
    inp = _minimal_inp(catalog_slice=sl)
    return ("c1",), reserved, {"c1": cand}, inp


# --- Task 1 / 5: AST import boundaries (B-CS3-1, B-CS3-9) ---


def test_b_cs3_validation_modules_forbidden_imports_ast() -> None:
    violations: list[str] = []
    for module_path in _VALIDATION_MODULE_PATHS:
        violations.extend(_forbidden_imports(module_path))
    assert violations == [], "\n".join(violations)


@pytest.mark.parametrize("path", _VALIDATION_MODULE_PATHS, ids=lambda p: p.name)
def test_b_cs3_validation_modules_no_solver_run_orm_tokens_supplementary(path: Path) -> None:
    """Supplementary token scan — AST import test is PASS authority."""
    text = path.read_text(encoding="utf-8-sig")
    assert "SolverRun" not in text
    assert "config_json" not in text


# --- Task 2: immutability sentinels (B-CS3-2, B-CS3-5, B-CS3-10) ---


def test_b_cs3_validate_catalog_placements_preserves_candidate_and_catalog_slice() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    occupied = frozenset({(5, 7), (6, 7)})
    cand = _candidate(occupied=occupied, ref=ref)
    sl_before = copy.deepcopy(sl)
    cand_before = copy.deepcopy(cand)
    validate_catalog_placements(("c1",), {"c1": cand}, sl)
    assert sl == sl_before
    assert cand.occupied_cells == cand_before.occupied_cells
    assert cand.catalog_placement_ref == cand_before.catalog_placement_ref


def test_b_cs3_validate_final_layout_preserves_five_input_classes() -> None:
    committed_ids, reserved, candidates_by_id, inp = _valid_layout_fixtures()
    committed_before = copy.deepcopy(committed_ids)
    reserved_before = copy.deepcopy(reserved)
    candidates_before = copy.deepcopy(candidates_by_id)
    inp_before = copy.deepcopy(inp)

    result = validate_final_layout(committed_ids, reserved, candidates_by_id, inp)

    assert isinstance(result, bool)
    assert committed_ids == committed_before
    assert reserved == reserved_before
    assert candidates_by_id["c1"].occupied_cells == candidates_before["c1"].occupied_cells
    assert candidates_by_id["c1"].reachable == candidates_before["c1"].reachable
    assert inp.mineable_cells == inp_before.mineable_cells


def test_b_cs3_observe_only_still_invokes_final_layout(monkeypatch: pytest.MonkeyPatch) -> None:
    committed_ids, reserved, candidates_by_id, inp = _valid_layout_fixtures()
    calls: list[str] = []

    def _spy(*args: object, **kwargs: object) -> bool:
        calls.append("final")
        return True

    monkeypatch.setattr(
        "django_apps.asteroid_lab.optimization.validation.catalog_layout_validation.validate_final_layout",
        _spy,
    )
    passed, catalog_result = validate_pipeline_layout(
        committed_ids=committed_ids,
        reserved_route_cells=reserved,
        candidates_by_id=candidates_by_id,
        inp=inp,
        catalog_mode="observe_only",
    )
    assert calls == ["final"]
    assert passed is True
    assert catalog_result is None


# --- Task 3: reachable + no re-probe (B-CS3-3, B-CS3-6) ---


def test_b_cs3_validate_final_layout_does_not_call_route_probe() -> None:
    committed_ids, reserved, candidates_by_id, inp = _valid_layout_fixtures()

    def _boom(*args: object, **kwargs: object) -> object:
        raise ValidationBoundaryViolation("route_probe called from validation")

    with patch(
        "django_apps.asteroid_lab.optimization.routing.route_probe.probe_route",
        side_effect=_boom,
    ):
        validate_final_layout(committed_ids, reserved, candidates_by_id, inp)


def test_b_cs3_reachable_is_snapshot_assert_not_reprobe() -> None:
    committed_ids, reserved, candidates_by_id, inp = _valid_layout_fixtures()
    cand_ok = candidates_by_id["c1"]
    cand_bad = replace(cand_ok, reachable=False)
    assert validate_final_layout(committed_ids, reserved, {"c1": cand_ok}, inp) is True
    assert validate_final_layout(committed_ids, reserved, {"c1": cand_bad}, inp) is False


# --- Task 4: pipeline ordering (B-CS3-7, B-CS3-8) ---


def _function_body_line_range(path: Path, func_name: str) -> tuple[int, int]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            assert node.end_lineno is not None
            return node.lineno, node.end_lineno
    raise AssertionError(f"{func_name} not found in {path.name}")


def _first_call_line(path: Path, func_name: str, callee: str) -> int:
    start, end = _function_body_line_range(path, func_name)
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for lineno in range(start, end + 1):
        if callee in lines[lineno - 1]:
            return lineno
    raise AssertionError(f"{callee} not found in {func_name}")


def test_b_cs3_normal_pipeline_validation_after_commit_and_lns() -> None:
    commit_line = _first_call_line(_PIPELINE_PATH, "_run_v01_rttp_pipeline", "incremental_commit(")
    lns_line = _first_call_line(_PIPELINE_PATH, "_run_v01_rttp_pipeline", "run_local_lns(")
    validate_line = _first_call_line(
        _PIPELINE_PATH, "_run_v01_rttp_pipeline", "validate_pipeline_layout("
    )
    assert commit_line < lns_line < validate_line


def test_b_cs3_macro_pipeline_validation_after_commit_without_lns() -> None:
    commit_line = _first_call_line(
        _PIPELINE_PATH, "_run_macro_rttp_pipeline", "incremental_commit_macro("
    )
    validate_line = _first_call_line(
        _PIPELINE_PATH, "_run_macro_rttp_pipeline", "validate_macro_layout("
    )
    assert commit_line < validate_line
    start, end = _function_body_line_range(_PIPELINE_PATH, "_run_macro_rttp_pipeline")
    lines = _PIPELINE_PATH.read_text(encoding="utf-8-sig").splitlines()
    macro_body = "\n".join(lines[start - 1 : end])
    assert "run_local_lns" not in macro_body
