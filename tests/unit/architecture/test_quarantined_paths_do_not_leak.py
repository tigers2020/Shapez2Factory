"""PR-D / PR-E / PR-F — quarantine registry gates (stale path isolation).

Spec: docs/superpowers/specs/2026-05-24-decontamination-pr-d-quarantine-design.md
PR-E: docs/superpowers/specs/2026-05-24-decontamination-pr-e-dead-code-design.md
PR-F: docs/superpowers/specs/2026-05-30-test-cleanup-aggressive-decontamination-design.md
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.unit.architecture.quarantine_registry import (
    _INTERNAL_IMPORT_PREFIX,
    ACTIVE_RUNTIME_ROOTS,
    MAX_TRANSITIVE_IMPORT_DEPTH,
    PR_E_APPLIED_DELETIONS,
    PR_E_DELETE_CANDIDATES,
    PR_F_AGGRESSIVE_AUDIT_CANDIDATES,
    PR_F_APPLIED_DELETIONS,
    PR_F_APPROVED_DELETIONS,
    PR_F_PROTECTED_TESTS,
    QUARANTINED_DOC_PATHS,
    QUARANTINED_MODULE_PREFIXES,
    VALID_INVENTORY_GRADES,
    path_matches_protected,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _repo_path(rel: str) -> Path:
    return _REPO_ROOT / Path(rel)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))


def _import_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def _module_to_file(module: str) -> Path | None:
    if not module.startswith(_INTERNAL_IMPORT_PREFIX):
        return None
    rel = module.replace(".", "/") + ".py"
    candidate = _REPO_ROOT / rel
    if candidate.is_file():
        return candidate
    init_candidate = _REPO_ROOT / rel.replace(".py", "/__init__.py")
    if init_candidate.is_file():
        return init_candidate
    return None


def _collect_bounded_imports(root_file: Path, max_depth: int) -> list[tuple[str, str]]:
    """Return (module, source_rel) for root direct + transitive django_apps.asteroid_lab imports."""
    seen_files: set[Path] = set()
    collected: list[tuple[str, str]] = []
    queue: list[tuple[Path, int]] = [(root_file, 0)]

    while queue:
        path, depth = queue.pop(0)
        if path in seen_files or not path.is_file():
            continue
        seen_files.add(path)
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for module in _import_modules(_parse(path)):
            collected.append((module, rel))
            if depth >= max_depth:
                continue
            if not module.startswith(_INTERNAL_IMPORT_PREFIX):
                continue
            child = _module_to_file(module)
            if child is not None and child not in seen_files:
                queue.append((child, depth + 1))
    return collected


def _matches_quarantined_prefix(module: str, prefix: str) -> bool:
    if prefix in ("solver_runtime_pipeline", "pass_first", "shapez_asteroid"):
        return prefix in module
    return module == prefix or module.startswith(prefix + ".")


def _split_pytest_nodeid(nodeid: str) -> tuple[str, str]:
    if "::" not in nodeid:
        raise ValueError(f"expected pytest nodeid, got: {nodeid!r}")
    file_part, func_part = nodeid.split("::", 1)
    return file_part, func_part


def _function_defined_in_module(module_rel: str, func_name: str) -> bool:
    path = _repo_path(module_rel)
    assert path.is_file(), f"missing module for node check: {module_rel}"
    tree = _parse(path)
    return any(isinstance(node, ast.FunctionDef) and node.name == func_name for node in tree.body)


def _replacement_exists(replacement: str) -> bool:
    if "::" in replacement:
        module_rel, func_name = _split_pytest_nodeid(replacement)
        return _function_defined_in_module(module_rel, func_name)
    return _repo_path(replacement).is_file()


def test_quarantined_modules_are_declared_in_registry() -> None:
    prefix_ids = [e.id for e in QUARANTINED_MODULE_PREFIXES]
    doc_ids = [e.id for e in QUARANTINED_DOC_PATHS]
    assert len(prefix_ids) == len(set(prefix_ids))
    assert len(doc_ids) == len(set(doc_ids))
    for entry in QUARANTINED_MODULE_PREFIXES:
        assert entry.prefix
        assert entry.reason.strip()
    for entry in QUARANTINED_DOC_PATHS:
        assert entry.path
        assert entry.reason.strip()


def test_active_runtime_paths_do_not_import_quarantined_modules() -> None:
    violations: list[str] = []
    for rel in ACTIVE_RUNTIME_ROOTS:
        root = _repo_path(rel)
        assert root.is_file(), f"missing active runtime root: {rel}"
        for module, source in _collect_bounded_imports(root, MAX_TRANSITIVE_IMPORT_DEPTH):
            for entry in QUARANTINED_MODULE_PREFIXES:
                if _matches_quarantined_prefix(module, entry.prefix):
                    violations.append(
                        f"{source}: imports {module!r} — quarantined prefix {entry.id!r}"
                    )
    assert violations == []


def test_quarantined_doc_paths_have_disposition() -> None:
    missing: list[str] = []
    for entry in QUARANTINED_DOC_PATHS:
        tree = _repo_path(entry.path)
        assert tree.is_dir(), f"missing doc tree: {entry.path}"
        if entry.front_matter_scope == "readme_only":
            md_files = [tree / "README.md"]
        else:
            md_files = sorted(tree.rglob("*.md"))
        for md in md_files:
            try:
                text = md.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                missing.append(
                    f"{md.relative_to(_REPO_ROOT).as_posix()} (non-UTF-8 — fix or exclude)"
                )
                continue
            if "do_not_use_as_authority: true" not in text:
                missing.append(md.relative_to(_REPO_ROOT).as_posix())
    assert missing == [], "Add YAML front matter with do_not_use_as_authority: true: " + ", ".join(
        missing
    )


def test_pr_e_delete_candidates_empty() -> None:
    assert PR_E_DELETE_CANDIDATES == ()


def test_pr_e_applied_deletions_recorded() -> None:
    assert len(PR_E_APPLIED_DELETIONS) == 3
    paths = [entry.path for entry in PR_E_APPLIED_DELETIONS]
    assert len(paths) == len(set(paths))
    for entry in PR_E_APPLIED_DELETIONS:
        assert entry.kind in ("file", "pytest_node")
        assert entry.reason.strip()
        assert entry.evidence.strip()
        assert isinstance(entry.replacements, tuple)


def test_pr_e_applied_files_absent() -> None:
    missing: list[str] = []
    for entry in PR_E_APPLIED_DELETIONS:
        if entry.kind != "file":
            continue
        if _repo_path(entry.path).is_file():
            missing.append(entry.path)
    assert missing == [], f"deleted files still on disk: {missing}"


def test_pr_e_applied_pytest_nodes_absent() -> None:
    missing: list[str] = []
    for entry in PR_E_APPLIED_DELETIONS:
        if entry.kind != "pytest_node":
            continue
        module_rel, func_name = _split_pytest_nodeid(entry.path)
        if _function_defined_in_module(module_rel, func_name):
            missing.append(entry.path)
    assert missing == [], f"deleted pytest nodes still defined: {missing}"


def test_pr_e_replacement_targets_exist() -> None:
    missing: list[str] = []
    for entry in PR_E_APPLIED_DELETIONS:
        for replacement in entry.replacements:
            if not _replacement_exists(replacement):
                missing.append(f"{entry.path} -> {replacement}")
    assert missing == [], f"missing replacements: {missing}"


def test_pr_f_audit_candidates_have_valid_grades() -> None:
    assert len(PR_F_AGGRESSIVE_AUDIT_CANDIDATES) >= 200
    ids = [entry.id for entry in PR_F_AGGRESSIVE_AUDIT_CANDIDATES]
    assert len(ids) == len(set(ids))
    for entry in PR_F_AGGRESSIVE_AUDIT_CANDIDATES:
        assert entry.grade in VALID_INVENTORY_GRADES
        assert entry.path.strip()
        assert entry.reason.strip()
        assert entry.evidence.strip()


def test_pr_f_approved_deletions_empty_on_f0() -> None:
    assert PR_F_APPROVED_DELETIONS == ()
    assert PR_F_APPLIED_DELETIONS == ()


def test_pr_f_no_intent_unknown_after_f2() -> None:
    unknown = [e.path for e in PR_F_AGGRESSIVE_AUDIT_CANDIDATES if e.grade == "INTENT_UNKNOWN"]
    assert unknown == [], f"resolve via F2+ human review before merge: {unknown}"


def test_pr_f_protected_tests_non_empty() -> None:
    assert len(PR_F_PROTECTED_TESTS) >= 10
    for entry in PR_F_PROTECTED_TESTS:
        assert entry.strip()


def test_pr_f_approved_never_overlaps_protected() -> None:
    overlaps: list[str] = []
    for entry in PR_F_APPROVED_DELETIONS:
        for protected in PR_F_PROTECTED_TESTS:
            if path_matches_protected(entry.path, protected):
                overlaps.append(f"{entry.path} vs {protected}")
    assert overlaps == []


def test_pr_f_applied_replacements_exist() -> None:
    missing: list[str] = []
    for entry in PR_F_APPLIED_DELETIONS:
        for replacement in entry.replacements:
            if not _replacement_exists(replacement):
                missing.append(f"{entry.path} -> {replacement}")
    assert missing == [], f"missing PR-F replacements: {missing}"


def test_pr_f_delete_grades_do_not_overlap_protected() -> None:
    delete_grades = frozenset({"DUPLICATE_COVERAGE", "OBSOLETE_PRODUCT_PATH", "BROKEN_OR_DEAD"})
    overlaps: list[str] = []
    for entry in PR_F_AGGRESSIVE_AUDIT_CANDIDATES:
        if entry.grade not in delete_grades:
            continue
        for protected in PR_F_PROTECTED_TESTS:
            if path_matches_protected(entry.path, protected):
                overlaps.append(f"{entry.id}: {entry.path} vs {protected}")
    assert overlaps == []


def test_quarantine_gate_separate_from_reconstruction_decontamination() -> None:
    """PR-D import scan is bounded; P0 absence gate owns optimization/** deletion."""
    opt_root = _repo_path("django_apps/asteroid_lab/optimization")
    assert not opt_root.exists(), "optimization/ removed — use reconstruction decontamination gates"
    recon_gate = _repo_path("tests/unit/architecture/test_reconstruction_decontamination_gates.py")
    pr_d_test = _repo_path("tests/unit/architecture/test_quarantined_paths_do_not_leak.py")
    assert recon_gate.is_file() and pr_d_test.is_file()
    assert recon_gate != pr_d_test
