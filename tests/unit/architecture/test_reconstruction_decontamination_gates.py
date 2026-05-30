"""P0 decontamination — reconstruction slice gates (GATE-R1, GATE-R6, RTTP symbol)."""

from __future__ import annotations

import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_OPT = _REPO / "django_apps" / "asteroid_lab" / "optimization"
_CAT = _REPO / "django_apps" / "asteroid_lab" / "catalog"
_RECON = _REPO / "django_apps" / "asteroid_lab" / "reconstruction"


def test_optimization_package_absent() -> None:
    assert not _OPT.exists(), "optimization/ must be deleted (GATE-R1)"


def test_catalog_package_absent() -> None:
    assert not _CAT.exists(), "catalog/ must be deleted (GATE-R1)"


def test_reconstruction_imports_no_optimization() -> None:
    text = "\n".join(p.read_text(encoding="utf-8") for p in _RECON.rglob("*.py"))
    assert "django_apps.asteroid_lab.optimization" not in text
    assert "django_apps.asteroid_lab.catalog" not in text


def test_no_run_rttp_pipeline_in_runtime_code() -> None:
    """GATE-R3 (code): no RTTP pipeline symbol in django_apps/harness/src Python."""
    proc = subprocess.run(
        [
            "rg",
            "run_rttp_pipeline",
            "django_apps",
            "harness",
            "src",
            "-g",
            "*.py",
        ],
        cwd=_REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert proc.returncode == 1, proc.stdout  # rg exit 1 = no matches
