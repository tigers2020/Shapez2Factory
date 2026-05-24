"""PR-D quarantine registry — machine-readable stale path isolation.

Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-d-quarantine-design.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OwnerNextStep = Literal["PR-E", "maintain", "none"]


@dataclass(frozen=True, slots=True)
class QuarantineModulePrefix:
    id: str
    prefix: str
    reason: str
    replacement: str | None
    owner_next_step: OwnerNextStep = "maintain"


@dataclass(frozen=True, slots=True)
class QuarantineDocPath:
    id: str
    path: str
    reason: str
    replacement: str | None
    delete_candidate: bool = False
    owner_next_step: OwnerNextStep = "maintain"
    # all_md: every *.md under path; readme_only: series index only (legacy encodings elsewhere)
    front_matter_scope: Literal["all_md", "readme_only"] = "all_md"


# AST import graph checks (active runtime roots — see test_quarantined_paths_do_not_leak).
QUARANTINED_MODULE_PREFIXES: tuple[QuarantineModulePrefix, ...] = (
    QuarantineModulePrefix(
        id="revival-shapez-asteroid",
        prefix="django_apps.shapez_asteroid",
        reason="Package removed; inventory forbids revival",
        replacement="django_apps.asteroid_lab",
    ),
    QuarantineModulePrefix(
        id="revival-shapez-asteroid-short",
        prefix="shapez_asteroid",
        reason="Legacy namespace token",
        replacement="django_apps.asteroid_lab",
    ),
    QuarantineModulePrefix(
        id="revival-solver-runtime-pipeline",
        prefix="solver_runtime_pipeline",
        reason="Monolith pipeline removed (strip-solver)",
        replacement="django_apps.asteroid_lab.optimization.pipeline",
    ),
    QuarantineModulePrefix(
        id="revival-pass-first",
        prefix="pass_first",
        reason="Legacy pass-first path family",
        replacement="django_apps.asteroid_lab.optimization.pipeline",
    ),
)

# Document tree checks (front matter / stale authority — not importable).
QUARANTINED_DOC_PATHS: tuple[QuarantineDocPath, ...] = (
    QuarantineDocPath(
        id="doc-plans-asteroid-lab-optimization",
        path="documents/plans/asteroid_lab_optimization",
        reason="Inventory QUARANTINE; pre-RTTP plan snapshots",
        replacement="documents/Algorithm/asteroid_lab_*.md + docs/superpowers/specs/",
        delete_candidate=False,
        owner_next_step="maintain",
    ),
    QuarantineDocPath(
        id="doc-algorithm-solver-runtime-series",
        path="documents/Algorithm/solver_runtime",
        reason="ARCHIVED Phase A–M orchestration series",
        replacement="django_apps/asteroid_lab/optimization/ + RTTP specs",
        delete_candidate=False,
        owner_next_step="maintain",
        front_matter_scope="readme_only",
    ),
)

# PR-E may delete these paths; PR-D must not remove them.
PR_E_DELETE_CANDIDATES: tuple[str, ...] = (
    "tests/unit/asteroid_lab/test_service_import_boundaries.py",
)

# Closed set — extend only via spec amendment.
ACTIVE_RUNTIME_ROOTS: tuple[str, ...] = (
    "django_apps/asteroid_lab/services/solver_runtime_entry.py",
    "django_apps/asteroid_lab/optimization/pipeline.py",
    "django_apps/asteroid_lab/optimization/reconstruction_adapter.py",
    "django_apps/asteroid_lab/management/commands/run_solver.py",
    "django_apps/web/views/public_pages.py",
)

MAX_TRANSITIVE_IMPORT_DEPTH: int = 2
_INTERNAL_IMPORT_PREFIX: str = "django_apps.asteroid_lab."
