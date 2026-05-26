"""Regenerate PR-F inventory artifacts (run from repo root).

Writes:
  var/log/pr_f0_audit_entries.py  — paste into quarantine_registry via _merge_pr_f_registry.py
  var/log/pr_f0_report_tables.md  — per-package tables for inventory report

Not a CI gate. See docs/superpowers/specs/
2026-05-30-test-cleanup-aggressive-decontamination-design.md
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFERRED_MACRO_FILES = frozenset(
    {
        "test_rttp_macro_bundle_t3.py",
        "test_rttp_pipeline_macro_greenfield.py",
        "test_rttp_db_macro_integration.py",
    }
)
DEFERRED_G3 = frozenset({"test_coordinate_frame_equivalence.py"})
# Resolved PR-F2 (2026-05-30): both promoted to PROTECTED_CONTRACT in registry.
INTENT_UNKNOWN_FILES: frozenset[str] = frozenset()
ENV_GUARD_GAME_DATA = frozenset(
    {
        "test_admin_browse.py",
        "test_cross_references.py",
        "test_speed_dump_shapes.py",
        "test_source_object_coverage.py",
        "test_lazy_localized_text.py",
        "fixtures.py",
    }
)


def package_of(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] == "tests" and len(parts) >= 2:
        if parts[1] == "unit" and len(parts) >= 3:
            return f"unit/{parts[2]}"
        return parts[1]
    return "other"


def classify(rel: str) -> tuple[str, str, str | None, str | None]:
    rel = rel.replace("\\", "/")
    base = Path(rel).name

    if rel.startswith("tests/unit/architecture/"):
        return (
            "PROTECTED_CONTRACT",
            "Architecture / quarantine / contamination gates",
            None,
            None,
        )

    if base in DEFERRED_MACRO_FILES:
        return (
            "DEFERRED_FEATURE_TEST",
            "PR-B macro 4x4 pause; permanent skip until child-pool fixture",
            None,
            None,
        )
    if base in DEFERRED_G3:
        return (
            "DEFERRED_FEATURE_TEST",
            "G3 coordinate equivalence xfail gate (strict=True)",
            None,
            None,
        )
    if base in INTENT_UNKNOWN_FILES:
        rep = (
            "tests/unit/asteroid_lab/test_lab_rttp_snapshot_compose.py"
            if "unified_replay" in base
            else None
        )
        return (
            "INTENT_UNKNOWN",
            "Helper vs obsolete product path — human review before F2",
            rep,
            None,
        )

    if package_of(rel) == "unit/game_data" and base in ENV_GUARD_GAME_DATA:
        return (
            "ENV_GUARD_SKIP",
            "Conditional pytest.skip when pinned dump / seed missing",
            None,
            None,
        )

    if rel.startswith("tests/integration/"):
        return (
            "PROTECTED_CONTRACT",
            "HTTP / DB integration smoke for active routes",
            None,
            None,
        )
    if rel.startswith("tests/unit/web/"):
        return (
            "PROTECTED_CONTRACT",
            "Lab template / page context / replay JS contracts",
            None,
            None,
        )
    if rel.startswith("tests/unit/shapez_solver/") or rel.startswith("tests/unit/shapez_core/"):
        return (
            "PROTECTED_CONTRACT",
            "Recipe graph / shape core public contracts",
            None,
            None,
        )
    if rel.startswith("tests/unit/config/") or rel.startswith("tests/unit/test_"):
        return ("PROTECTED_CONTRACT", "Top-level unit contract gate", None, None)
    if rel.startswith("tests/unit/game_data/"):
        return (
            "PROTECTED_CONTRACT",
            "game_data import / catalog / provenance contracts",
            None,
            None,
        )

    if rel.startswith("tests/unit/asteroid_lab/"):
        return (
            "PROTECTED_CONTRACT",
            "Asteroid lab domain contract (default protect in F0)",
            None,
            None,
        )

    return ("INTENT_UNKNOWN", "Unclassified test path", None, None)


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def format_audit_entries(files: list[str]) -> str:
    lines = ["PR_F_AGGRESSIVE_AUDIT_CANDIDATES: tuple[PrFAuditEntry, ...] = ("]
    for i, rel in enumerate(files):
        grade, reason, replacement, target_slice = classify(rel)
        eid = f"f0-{i:03d}-{rel.replace('/', '-').replace('.py', '')[:48]}"
        rep = "None" if replacement is None else f'"{_escape(replacement)}"'
        sl = "None" if target_slice is None else f'"{target_slice}"'
        lines.append("    PrFAuditEntry(")
        lines.append(f'        id="{_escape(eid)}",')
        lines.append(f'        path="{_escape(rel)}",')
        lines.append('        kind="file",')
        lines.append(f'        grade="{grade}",')
        lines.append(f'        package="{_escape(package_of(rel))}",')
        lines.append(f'        reason="{_escape(reason)}",')
        lines.append(f"        replacement={rep},")
        lines.append(f"        target_slice={sl},")
        lines.append(f'        evidence="F0 inventory classify {rel}",')
        lines.append("    ),")
    lines.append(")")
    return "\n".join(lines)


def format_report_tables(files: list[str]) -> str:
    by_pkg: dict[str, list[str]] = {}
    for rel in files:
        by_pkg.setdefault(package_of(rel), []).append(rel)
    chunks = []
    for pkg in sorted(by_pkg):
        chunks.append(f"### `{pkg}` ({len(by_pkg[pkg])} files)\n")
        chunks.append("| path | grade | reason |")
        chunks.append("|------|-------|--------|")
        for rel in sorted(by_pkg[pkg]):
            grade, reason, _, _ = classify(rel)
            chunks.append(f"| `{rel}` | `{grade}` | {reason} |")
        chunks.append("")
    return "\n".join(chunks)


def main() -> None:
    files = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("tests/**/test_*.py"))
    grades: dict[str, int] = {}
    for rel in files:
        g, *_ = classify(rel)
        grades[g] = grades.get(g, 0) + 1
    out = ROOT / "var" / "log" / "pr_f0_audit_entries.py"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_audit_entries(files) + "\n", encoding="utf-8")
    report = ROOT / "var" / "log" / "pr_f0_report_tables.md"
    report.write_text(format_report_tables(files), encoding="utf-8")
    print("grade_counts", grades)
    print("total", len(files))
    print("wrote", out)
    print("wrote", report)


if __name__ == "__main__":
    main()
