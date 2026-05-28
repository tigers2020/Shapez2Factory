"""Layer post-summary JSONL logging (flag-gated)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.test import override_settings

from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_post_summary import LayerPostSummaryOutcome
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_01_RECONSTRUCTION,
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
)
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.observability.layer_post_summary_log import (
    create_layer_post_summary_log_session,
)
from django_apps.asteroid_lab.layers.stack_runner import (
    _Layer02To05Runner,
    run_full_from_cleanup_recon,
    run_layers_02_to_05,
)
from tests.unit.asteroid_lab.layers.test_stack_runner_skeleton import _canon_complete_map


def test_create_session_returns_none_when_flag_disabled() -> None:
    assert create_layer_post_summary_log_session() is None


@override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED=True)
def test_create_session_returns_session_when_flag_enabled(tmp_path: Path) -> None:
    with override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR=tmp_path):
        session = create_layer_post_summary_log_session(project_slug="demo-slug")
    assert session is not None
    assert session.project_slug == "demo-slug"
    assert session.run_dir.is_dir()


@override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED=True)
def test_run_layers_writes_per_layer_post_summary_jsonl(tmp_path: Path) -> None:
    calls: list[str] = []

    def _mk(slug: str) -> _Layer02To05Runner:
        def _run(**_kwargs: object) -> None:
            calls.append(slug)

        return _Layer02To05Runner(slug, _run)

    runners = (
        _mk(LAYER_02_EXTERIOR_TRANSPORT),
        _mk(LAYER_03_RIM_MINING_BUNDLES),
    )
    with override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR=tmp_path):
        session = create_layer_post_summary_log_session(run_id="test-run-02-03")
        assert session is not None
        complete = _canon_complete_map()
        ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
        result = run_layers_02_to_05(
            complete_map=complete,
            budget_ctx=ctx,
            runners=runners,
            post_summary_session=session,
        )
        session.close(result)

    assert calls == [LAYER_02_EXTERIOR_TRANSPORT, LAYER_03_RIM_MINING_BUNDLES]
    l2_path = session.run_dir / f"{LAYER_02_EXTERIOR_TRANSPORT}.post_summary.jsonl"
    assert l2_path.is_file()
    l2_row = json.loads(l2_path.read_text(encoding="utf-8").strip())
    assert l2_row["record_type"] == "layer_post_summary"
    assert l2_row["outcome"] == LayerPostSummaryOutcome.COMPLETED.value
    assert l2_row["layer_index"] == 2
    assert "remaining_budget_ms" in l2_row

    stack_path = session.run_dir / "stack_run.post_summary.jsonl"
    stack_row = json.loads(stack_path.read_text(encoding="utf-8").strip())
    assert stack_row["stack_run_status"] == StackRunStatus.SUCCESS.value


@override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED=True)
def test_timeout_writes_skipped_budget_post_summary(tmp_path: Path) -> None:
    runners = (
        _Layer02To05Runner(LAYER_02_EXTERIOR_TRANSPORT, lambda **_k: None),
        _Layer02To05Runner(LAYER_03_RIM_MINING_BUNDLES, lambda **_k: None),
    )
    with override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR=tmp_path):
        session = create_layer_post_summary_log_session(run_id="test-timeout")
        assert session is not None
        complete = _canon_complete_map()
        ctx = LayerBudgetContext(
            deadline_monotonic=100.0,
            started_monotonic=0.0,
            now_fn=lambda: 100.0,
        )
        result = run_layers_02_to_05(
            complete_map=complete,
            budget_ctx=ctx,
            runners=runners,
            post_summary_session=session,
        )
        session.close(result)

    assert result.status == StackRunStatus.TIMEOUT_FAIL_CLOSED
    skip_path = session.run_dir / f"{LAYER_02_EXTERIOR_TRANSPORT}.post_summary.jsonl"
    skip_row = json.loads(skip_path.read_text(encoding="utf-8").strip())
    assert skip_row["outcome"] == LayerPostSummaryOutcome.SKIPPED_BUDGET.value


@pytest.mark.django_db
@override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_ENABLED=True)
def test_run_full_writes_layer01_and_stack_manifest(
    tmp_path: Path,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
    from django_apps.asteroid_lab.layers.stack_runner import _Layer02To05Runner
    from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
    from django_apps.asteroid_lab.reconstruction.topology_contract import (
        decode_shapez_copy_string,
        load_reconstruction_fixture_line_pairs,
    )

    required_copy, _ = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    runners = (_Layer02To05Runner(LAYER_02_EXTERIOR_TRANSPORT, lambda **_k: None),)

    with override_settings(ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_DIR=tmp_path):
        _, stack = run_full_from_cleanup_recon(
            cleanup=cleanup,
            recon=recon,
            budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
            runners=runners,
            project_slug="fixture-project",
        )

    assert stack.status == StackRunStatus.SUCCESS
    run_dirs = list((tmp_path / "runs").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    l1_path = run_dir / f"{LAYER_01_RECONSTRUCTION}.post_summary.jsonl"
    assert l1_path.is_file()
    l1_row = json.loads(l1_path.read_text(encoding="utf-8").strip())
    assert l1_row["layer_index"] == 1
    assert l1_row["remaining_budget_ms"] is None
    assert "complete_map_cell_count" in l1_row["metrics"]
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["stack_run_status"] == StackRunStatus.SUCCESS.value
