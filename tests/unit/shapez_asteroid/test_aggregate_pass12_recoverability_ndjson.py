"""CLI aggregate for pass12 recoverability histograms from NDJSON."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "debug" / "aggregate_pass12_recoverability_from_ndjson.py"


@pytest.mark.unit
def test_aggregate_pass12_recoverability_merges_two_rows(tmp_path: Path) -> None:
    p = tmp_path / "trace.ndjson"
    rows = [
        {
            "kind": "trace",
            "message": "solver_summary",
            "data": {
                "solver_summary": {
                    "pass12_recoverability_class_counts": {"TRIVIAL": 1, "NEAR_TRANSPORT": 2}
                }
            },
        },
        {
            "kind": "trace",
            "message": "solver_summary",
            "data": {
                "solver_summary": {
                    "pass12_recoverability_class_counts": {"TRIVIAL": 3, "LOCAL_ROTATION": 1}
                }
            },
        },
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), str(p)],
        cwd=str(REPO_ROOT),
        text=True,
    )
    data = json.loads(out)
    assert data["total_runs"] == 2
    assert data["solver_summary_rows_used"] == 2
    assert data["files_scanned"] == 1
    assert data["pass12_recoverability_class_counts"]["TRIVIAL"] == 4
    assert data["class_counts"]["TRIVIAL"] == 4
    assert data["pass12_recoverability_class_counts"]["NEAR_TRANSPORT"] == 2
    assert data["pass12_recoverability_class_counts"]["LOCAL_ROTATION"] == 1
    assert data["reason_counts"] == {}
    assert data["avg_preserve_quality_score"] is None
    assert data["preserve_quality_score_percentiles"]["p50"] is None
    assert data["source_kind_breakdown"]["unknown"]["solver_summary_rows"] == 2


@pytest.mark.unit
def test_aggregate_pass12_replay_wire_solver_summary(tmp_path: Path) -> None:
    """Replay wire rows (no kind: trace) aggregate like legacy debug-wrapped lines."""

    p = tmp_path / "replay.ndjson"
    rows = [
        {
            "location": "finalize",
            "message": "solver_summary",
            "data": {
                "run_id": "rwire",
                "solver_summary": {
                    "pass12_recoverability_class_counts": {"TRIVIAL": 2, "NEAR_TRANSPORT": 1}
                },
            },
        },
        {
            "location": "finalize",
            "message": "solver_summary",
            "data": {
                "run_id": "rwire",
                "ts": 1.0,
                "solver_summary": {
                    "pass12_recoverability_class_counts": {"TRIVIAL": 1, "LOCAL_ROTATION": 3}
                },
            },
        },
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), str(p)],
        cwd=str(REPO_ROOT),
        text=True,
    )
    data = json.loads(out)
    assert data["total_runs"] == 2
    assert data["pass12_recoverability_class_counts"]["TRIVIAL"] == 3
    assert data["pass12_recoverability_class_counts"]["NEAR_TRANSPORT"] == 1
    assert data["pass12_recoverability_class_counts"]["LOCAL_ROTATION"] == 3


@pytest.mark.unit
def test_aggregate_run_id_matches_data_run_id_on_replay_wire(tmp_path: Path) -> None:
    p = tmp_path / "t.ndjson"
    p.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "location": "x",
                        "message": "solver_summary",
                        "data": {
                            "run_id": "inner",
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"X": 1},
                            },
                        },
                    }
                ),
                json.dumps(
                    {
                        "location": "x",
                        "message": "solver_summary",
                        "data": {
                            "run_id": "other",
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"X": 99},
                            },
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), str(p), "--run-id", "inner"],
        cwd=str(REPO_ROOT),
        text=True,
    )
    data = json.loads(out)
    assert data["total_runs"] == 1
    assert data["pass12_recoverability_class_counts"]["X"] == 1


@pytest.mark.unit
def test_aggregate_respects_run_id_filter(tmp_path: Path) -> None:
    p = tmp_path / "t.ndjson"
    p.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "a",
                        "kind": "trace",
                        "message": "solver_summary",
                        "data": {
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"X": 10},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "run_id": "b",
                        "kind": "trace",
                        "message": "solver_summary",
                        "data": {
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"X": 99},
                            }
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), str(p), "--run-id", "b"],
        cwd=str(REPO_ROOT),
        text=True,
    )
    data = json.loads(out)
    assert data["total_runs"] == 1
    assert data["solver_summary_rows_used"] == 1
    assert data["pass12_recoverability_class_counts"]["X"] == 99


@pytest.mark.unit
def test_aggregate_split_by_ndjson_run_id(tmp_path: Path) -> None:
    p = tmp_path / "t.ndjson"
    p.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "r1",
                        "kind": "trace",
                        "message": "solver_summary",
                        "data": {
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"A": 1},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "run_id": "r1",
                        "kind": "trace",
                        "message": "solver_summary",
                        "data": {
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"A": 2},
                            }
                        },
                    }
                ),
                json.dumps(
                    {
                        "run_id": "r2",
                        "kind": "trace",
                        "message": "solver_summary",
                        "data": {
                            "solver_summary": {
                                "pass12_recoverability_class_counts": {"B": 5},
                            }
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), str(p), "--split-by-ndjson-run-id"],
        cwd=str(REPO_ROOT),
        text=True,
    )
    data = json.loads(out)
    assert data["pass12_recoverability_class_counts"]["A"] == 3
    assert data["pass12_recoverability_class_counts"]["B"] == 5
    by_run = data["pass12_recoverability_class_counts_by_ndjson_run_id"]
    assert by_run["r1"]["A"] == 3
    assert by_run["r2"]["B"] == 5
    assert data["total_runs"] == 3


@pytest.mark.unit
def test_aggregate_reasons_pqs_percentiles_and_source_kind(tmp_path: Path) -> None:
    p = tmp_path / "t.ndjson"
    rows = [
        {
            "kind": "trace",
            "message": "solver_summary",
            "data": {
                "solver_summary": {
                    "existing_layout_source_kind": "existing_fluid_layout",
                    "pass12_recoverability_class_counts": {"TRIVIAL": 1},
                    "pass12_preserve_drop_reason_counts": {"NO_MATCHING_STUB": 1},
                    "preserve_quality_score": 0.1,
                    "preserve_quality_score_version": 1,
                }
            },
        },
        {
            "kind": "trace",
            "message": "solver_summary",
            "data": {
                "solver_summary": {
                    "existing_layout_source_kind": "existing_shape_layout",
                    "pass12_recoverability_class_counts": {"TRIVIAL": 2},
                    "pass12_preserve_drop_reason_counts": {"NO_MATCHING_STUB": 2},
                    "preserve_quality_score": 0.9,
                    "preserve_quality_score_version": 1,
                }
            },
        },
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    out = subprocess.check_output(
        [sys.executable, str(SCRIPT), str(p)],
        cwd=str(REPO_ROOT),
        text=True,
    )
    data = json.loads(out)
    assert data["reason_counts"]["NO_MATCHING_STUB"] == 3
    assert data["avg_preserve_quality_score"] == pytest.approx(0.5, rel=0, abs=1e-6)
    pct = data["preserve_quality_score_percentiles"]
    assert pct["p50"] == pytest.approx(0.5, rel=0, abs=1e-5)
    assert pct["p90"] == pytest.approx(0.82, rel=0, abs=0.02)
    assert data["preserve_quality_score_version_counts"].get("1") == 2
    sk = data["source_kind_breakdown"]
    assert sk["existing_fluid_layout"]["solver_summary_rows"] == 1
    assert sk["existing_shape_layout"]["solver_summary_rows"] == 1
    assert sk["existing_fluid_layout"]["class_counts"]["TRIVIAL"] == 1
    assert sk["existing_shape_layout"]["class_counts"]["TRIVIAL"] == 2
