"""PR-3: golden solver run and replay-input boundary tests."""

from __future__ import annotations

import builtins
import importlib
from pathlib import Path
from unittest import mock

import pytest

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_fixtures import (
    golden_fixture_dir,
    load_empty_copy,
    load_game_data_rules,
    load_genetic_sample_seeds,
)
from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run import (
    GoldenSolverArtifacts,
    GoldenSolverConfig,
    run_golden_solver,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)

_FIXTURE_ROOT = golden_fixture_dir()


def _fixtures_ready() -> bool:
    return all(
        (_FIXTURE_ROOT / name).is_file()
        for name in (
            "empty.shapez.txt",
            "golden.shapez.txt",
            "game_data_snapshot_min.json",
            "genetic_sample_seeds.json",
        )
    )


def test_golden_solver_no_replay_input_static() -> None:
    mod = importlib.import_module(
        "shapez2_factory.application.asteroid_lab.experiments.golden_fixture_solver_run",
    )
    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "django_apps.asteroid_lab.replay" not in source
    assert "replay_service" not in source
    assert "var/runs" not in source
    assert ".jsonl" not in source


def _forbidden_replay_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    forbidden = (
        "/var/runs/",
        ".jsonl",
        "replay_core",
        "lab_replay",
    )
    return any(token in normalized for token in forbidden)


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_solver_no_replay_input_runtime() -> None:
    real_open = builtins.open
    real_path_open = Path.open
    real_read_text = Path.read_text

    def guarded_open(file: object, *args: object, **kwargs: object) -> object:
        if _forbidden_replay_path(str(file)):
            msg = f"forbidden replay input path: {file}"
            raise AssertionError(msg)
        return real_open(file, *args, **kwargs)

    def guarded_path_open(self: Path, *args: object, **kwargs: object) -> object:
        if _forbidden_replay_path(str(self)):
            msg = f"forbidden replay input path: {self}"
            raise AssertionError(msg)
        return real_path_open(self, *args, **kwargs)

    def guarded_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if _forbidden_replay_path(str(self)):
            msg = f"forbidden replay input path: {self}"
            raise AssertionError(msg)
        return real_read_text(self, *args, **kwargs)

    with (
        mock.patch("builtins.open", side_effect=guarded_open),
        mock.patch.object(Path, "open", guarded_path_open),
        mock.patch.object(Path, "read_text", guarded_read_text),
    ):
        artifacts = run_golden_solver(
            copy_text=load_empty_copy(),
            game_data_rules=load_game_data_rules(),
            genetic_sample_seeds=load_genetic_sample_seeds(),
            config=GoldenSolverConfig(budget_ms=60_000),
        )
    assert artifacts.core_result.stack_result is not None
    assert artifacts.complete_map is not None


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_stack_smoke() -> None:
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    assert isinstance(artifacts, GoldenSolverArtifacts)
    assert artifacts.core_result.stack_result.failed_layer_slug is None
    assert len(artifacts.layer_summaries) >= 4


@pytest.mark.skipif(not _fixtures_ready(), reason="asteroid_golden fixtures incomplete")
def test_golden_solver_artifacts_layer_fields() -> None:
    artifacts = run_golden_solver(
        copy_text=load_empty_copy(),
        game_data_rules=load_game_data_rules(),
        genetic_sample_seeds=load_genetic_sample_seeds(),
        config=GoldenSolverConfig(budget_ms=60_000),
    )
    slugs = {record.layer_slug for record in artifacts.layer_summaries}
    assert LAYER_02_EXTERIOR_TRANSPORT in slugs
    assert LAYER_03_RIM_GREEDY_PLACEMENT in slugs
    assert LAYER_04_INNER_PATTERN_FILL in slugs
    assert LAYER_05_TRANSPORT_ROUTING in slugs

    assert artifacts.exterior_plan is not None
    assert artifacts.rim_result is not None
    # L4/L5 may be empty on canonical empty map but must be structured when present.
    if artifacts.inner_fill is not None:
        assert hasattr(artifacts.inner_fill, "interior_occupied_cells")
    if artifacts.route_plan is not None:
        assert hasattr(artifacts.route_plan, "routes")
