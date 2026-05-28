"""G4 doc hygiene — RTTP must not appear as *active* authority on canon surfaces."""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]

# Surfaces agents read for "what to implement now" (not historical specs/plans).
_CANON_AUTHORITY_FILES = (
    "documents/ai/current_plan.md",
    "documents/ai/START_HERE.md",
    "documents/index/document_inventory.md",
    "documents/Algorithm/README.md",
    "documents/Algorithm/asteroid_lab_00_overview.md",
    "documents/Algorithm/asteroid_lab_09_replay_timeline.md",
    "documents/Algorithm/asteroid_lab_12_runtime_replay_wiring.md",
    "documents/Algorithm/asteroid_lab_13_replay_payload_scalability.md",
)


def _rg_hits(pattern: str, paths: tuple[str, ...]) -> str:
    proc = subprocess.run(
        ["rg", "-n", pattern, *paths, "--glob", "!documents/archive/**"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode == 1:
        return ""
    return proc.stdout.strip()


def test_no_rttp_hybrid_c_on_canon_authority_files() -> None:
    out = _rg_hits("RTTP Hybrid C", _CANON_AUTHORITY_FILES)
    assert not out, f"RTTP Hybrid C on canon authority files:\n{out}"


def test_no_active_optimization_runtime_on_canon_authority_files() -> None:
    """Allow 'optimization/ removed' forbids; forbid live runtime pointers."""
    out = _rg_hits(
        r"django_apps/asteroid_lab/optimization/(?!.*\b(removed|deleted|absent|RETIRED|Forbidden)\b)",
        _CANON_AUTHORITY_FILES,
    )
    # rg lacks PCRE lookahead on all platforms — filter lines manually
    if out:
        bad = [
            line
            for line in out.splitlines()
            if not any(
                tok in line.lower()
                for tok in ("removed", "deleted", "absent", "retired", "forbidden", "**removed**")
            )
        ]
        assert not bad, "live optimization/ pointer on canon files:\n" + "\n".join(bad)


def test_rttp_superpowers_specs_allowlist_only() -> None:
    specs = _REPO / "docs" / "superpowers" / "specs"
    if not specs.is_dir():
        return
    rttp_specs = sorted(p.name for p in specs.glob("*rttp*"))
    allowed = {
        "2026-05-27-rttp-mining-equipment-goal-contract-design.md",
    }
    extra = set(rttp_specs) - allowed
    assert not extra, f"Unexpected active *rttp* specs: {sorted(extra)}"


def test_inventory_marks_optimization_retired() -> None:
    text = (_REPO / "documents" / "index" / "document_inventory.md").read_text(encoding="utf-8")
    assert "optimization/` **removed**" in text or "optimization/` deleted" in text
    assert "RTTP Hybrid C pipeline" not in text
