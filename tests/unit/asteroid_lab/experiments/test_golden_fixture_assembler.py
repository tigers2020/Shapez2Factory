"""PR-6: candidate blueprint assembler tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_assembler import (
    assemble_candidate_blueprint,
    encode_candidate_copy_string,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
    load_empty_copy,
    load_game_data_rules,
    load_genetic_sample_seeds,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverConfig,
    run_golden_solver,
)
from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

_ASSEMBLER_SOURCE = (
    Path(__file__).resolve().parents[4]
    / "src"
    / "shapez2_factory"
    / "application"
    / "asteroid_lab"
    / "experiments"
    / "golden_fixture_assembler.py"
)
_FIXTURE_ROOT = golden_fixture_dir()


def _fixtures_ready() -> bool:
    return (_FIXTURE_ROOT / "empty.shapez.txt").is_file()


def test_assembler_does_not_read_golden_coordinates() -> None:
    source = _ASSEMBLER_SOURCE.read_text(encoding="utf-8")
    assert "golden.shapez" not in source
    assert "load_golden_copy" not in source
    assert "GoldenOracle" not in source
    assert "build_golden_oracle" not in source


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_assembler_output_is_deterministic() -> None:
    empty_copy = load_empty_copy()
    artifacts = run_golden_solver(
        copy_text=empty_copy,
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    first = encode_candidate_copy_string(artifacts=artifacts, empty_copy=empty_copy)
    second = encode_candidate_copy_string(artifacts=artifacts, empty_copy=empty_copy)
    assert first == second


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_assembler_decode_round_trip() -> None:
    empty_copy = load_empty_copy()
    artifacts = run_golden_solver(
        copy_text=empty_copy,
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    copy = encode_candidate_copy_string(artifacts=artifacts, empty_copy=empty_copy)
    assert copy.startswith("SHAPEZ2-4-")
    root = decode_copy_string(copy).root
    assert isinstance(root.get("BP"), dict)
    entries = root["BP"].get("Entries")
    assert isinstance(entries, list)
    expected_len = len(
        assemble_candidate_blueprint(artifacts=artifacts, empty_copy=empty_copy)["BP"]["Entries"],
    )
    assert len(entries) == expected_len
