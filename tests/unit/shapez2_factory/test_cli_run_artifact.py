"""PR-CLI-3b: pure CLI ``run`` writes a finalized artifact directory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_FILENAME,
    ArtifactManifest,
)
from shapez2_factory.interfaces.cli.asteroid_solve import ExitCode, main

_REPO = Path(__file__).resolve().parents[3]
_COPY_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "reconstruction_required_.txt"
_SNAPSHOT_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "game_data_snapshot_min.json"


def test_cli_run_writes_full_artifact_and_validates(tmp_path: Path) -> None:
    code = main(
        [
            "run",
            "--allowed-root",
            str(tmp_path),
            "--artifact-root",
            str(tmp_path),
            "--run-key",
            "cli-run-1",
            "--copy-file",
            str(_COPY_FIXTURE),
            "--snapshot",
            str(_SNAPSHOT_FIXTURE),
            "--budget-ms",
            "60000",
        ]
    )

    assert code == ExitCode.OK
    final = tmp_path / "cli-run-1"
    manifest = ArtifactManifest.from_json((final / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    assert set(manifest.paths) >= {
        "copy",
        "game_data_snapshot",
        "layer01_complete_map",
        "stack_result",
        "solver_summary",
        "replay_core",
    }
    assert set(manifest.content_hashes) >= set(manifest.paths.values())
    assert (
        json.loads((final / "output" / "stack_result.json").read_text(encoding="utf-8"))["status"]
        == "success"
    )
    complete_map = json.loads(
        (final / "output" / "layer01_complete_map.json").read_text(encoding="utf-8")
    )
    assert complete_map["schema_version"] == "complete_map_v1"
    assert complete_map["cells"]
    assert complete_map["field_cells"]
    solver_summary = json.loads(
        (final / "output" / "solver_summary.json").read_text(encoding="utf-8")
    )
    assert solver_summary["run_success"] is True
    assert solver_summary["validation_passed"] is True
    replay_lines = (final / "output" / "replay_core.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(replay_lines[0])["record_type"] == "header"
    assert [json.loads(line)["frame_index"] for line in replay_lines[1:]] == list(
        range(len(replay_lines) - 1)
    )
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.OK


def test_cli_run_verbose_emits_layer_lines(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "run",
            "--allowed-root",
            str(tmp_path),
            "--artifact-root",
            str(tmp_path),
            "--run-key",
            "cli-run-verbose",
            "--copy-file",
            str(_COPY_FIXTURE),
            "--snapshot",
            str(_SNAPSHOT_FIXTURE),
            "--verbose",
        ]
    )

    assert code == ExitCode.OK
    stderr = capsys.readouterr().err
    assert "asteroid_cli layer_done layer_slug=layer_02_exterior_transport" in stderr


def test_cli_run_default_omits_verbose_layer_lines(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(
        [
            "run",
            "--allowed-root",
            str(tmp_path),
            "--artifact-root",
            str(tmp_path),
            "--run-key",
            "cli-run-default",
            "--copy-file",
            str(_COPY_FIXTURE),
            "--snapshot",
            str(_SNAPSHOT_FIXTURE),
        ]
    )

    assert code == ExitCode.OK
    assert "asteroid_cli layer_done" not in capsys.readouterr().err
