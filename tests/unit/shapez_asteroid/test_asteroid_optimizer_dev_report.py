from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.shapez_asteroid.services.asteroid_optimizer_dev_report import (
    format_asteroid_optimizer_dev_report_md,
    resolve_dev_report_md_path,
    write_asteroid_optimizer_dev_report,
)


def test_resolve_dev_report_md_path_default() -> None:
    base = Path("/tmp/proj")
    p = resolve_dev_report_md_path(base_dir=base, override="")
    assert p == base / "var" / "asteroid_optimizer_dev_report.md"


def test_resolve_dev_report_md_path_relative_override() -> None:
    base = Path("/tmp/proj")
    p = resolve_dev_report_md_path(base_dir=base, override="out/x.md")
    assert p == base / "out" / "x.md"


def test_format_dev_report_contains_timeline_and_replay_histogram() -> None:
    md = format_asteroid_optimizer_dev_report_md(
        map_timeline=[
            {
                "id": "v2_recon_mineable",
                "summary": {
                    "entry_count": 3,
                    "phase": "v2_recon_mineable",
                    "preview_placeholder": "",
                },
                "mining_map": [],
            }
        ],
        root_summary={"entry_count": 3, "phase": "v2_final_layout"},
        reconstruction_summary={"mineable_placement_count": 1},
        mining_layout_engine="v2",
        include_solver_overlay=False,
        include_solver_replay=True,
        solver_timeline=[{"id": "solver_init"}],
        solver_replay={
            "contractVersion": 2,
            "events": [{"kind": "route"}, {"kind": "route"}, {"kind": "placement"}],
        },
        solver_layout_package_unavailable=False,
        mining_layout_runtime_flags=None,
        preview_schema_version=2,
        code_fingerprint="abc123",
    )
    assert "# Asteroid optimizer" in md
    assert "`v2_recon_mineable`" in md
    assert "| `route` | 2 |" in md
    assert "| `placement` | 1 |" in md
    assert "`abc123`" in md
    assert "## Solver timeline" in md
    assert "`solver_init`" in md


def test_write_asteroid_optimizer_dev_report_overwrites(tmp_path: Path) -> None:
    p = tmp_path / "r.md"
    write_asteroid_optimizer_dev_report(p, "first\n")
    assert p.read_text(encoding="utf-8") == "first\n"
    write_asteroid_optimizer_dev_report(p, "second\n")
    assert p.read_text(encoding="utf-8") == "second\n"


@pytest.mark.parametrize(
    ("preview_schema_version", "expect_line"),
    [
        (2, "- **preview_schema_version**: `2`"),
        (None, "- **preview_schema_version**: `None`"),
    ],
)
def test_format_preview_schema_version(
    preview_schema_version: int | None,
    expect_line: str,
) -> None:
    md = format_asteroid_optimizer_dev_report_md(
        map_timeline=[],
        root_summary={"entry_count": 0, "phase": "x"},
        reconstruction_summary=None,
        mining_layout_engine="v2",
        include_solver_overlay=False,
        include_solver_replay=False,
        solver_timeline=None,
        solver_replay=None,
        solver_layout_package_unavailable=False,
        mining_layout_runtime_flags=None,
        preview_schema_version=preview_schema_version,
        code_fingerprint=None,
    )
    assert expect_line in md
