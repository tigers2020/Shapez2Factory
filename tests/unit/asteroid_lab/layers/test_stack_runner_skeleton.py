"""stack_runner orchestration ??PR-1 skeleton."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
    LAYER_05_INNER_PATTERN_FILL,
    LAYER_06_COMMIT_VALIDATE,
)
from django_apps.asteroid_lab.layers.contracts.stack_status import StackRunStatus
from django_apps.asteroid_lab.layers.stack_runner import (
    _Layer02To05Runner,
    run_full_from_cleanup_recon,
    run_layers_02_to_05,
)
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from tests.support.reconstruction_complete_map_fixtures import complete_map_from_overlay_cells


def _canon_complete_map():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return build_reconstruction_complete_map(cleanup=cleanup, recon=recon)


@pytest.mark.django_db
def test_stack_runner_invokes_l1_then_l2_to_l6(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    calls: list[str] = []

    def _mk(slug: str) -> _Layer02To05Runner:
        def _run(**_kwargs: object) -> None:
            calls.append(slug)

        return _Layer02To05Runner(slug, _run)

    runners = (
        _mk(LAYER_02_EXTERIOR_TRANSPORT),
        _mk(LAYER_03_RIM_GREEDY_PLACEMENT),
        _mk(LAYER_05_INNER_PATTERN_FILL),
        _mk(LAYER_06_COMMIT_VALIDATE),
    )
    required_copy, _ = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    with patch(
        "django_apps.asteroid_lab.layers.stack_runner.run_layer_01",
    ) as run_layer_01_mock:
        from tests.support.reconstruction_complete_map_fixtures import (
            complete_map_from_overlay_cells,
        )

        cell = DecodedCellDTO(
            x=0,
            y=0,
            layer=None,
            rotation=0,
            tile_type="",
            cell_kind="asteroid_shape_field",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={},
        )
        complete = complete_map_from_overlay_cells(cell)
        from django_apps.asteroid_lab.layers.layer_01_reconstruction.output import (
            Layer01ReconstructionOutput,
        )

        run_layer_01_mock.return_value = Layer01ReconstructionOutput(
            complete_map=complete,
            capacity_envelope={"capacity_basis": "terrain_upper_bound"},
        )
        _, stack = run_full_from_cleanup_recon(
            cleanup=cleanup,
            recon=recon,
            budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
            runners=runners,
        )
    run_layer_01_mock.assert_called_once()
    assert stack.status == StackRunStatus.SUCCESS
    assert calls == [
        LAYER_02_EXTERIOR_TRANSPORT,
        LAYER_03_RIM_GREEDY_PLACEMENT,
        LAYER_05_INNER_PATTERN_FILL,
        LAYER_06_COMMIT_VALIDATE,
    ]
    assert LAYER_04_RIM_BUNDLE_PLACEMENT not in calls


def test_layer_06_registered_in_stack_runner_source() -> None:
    source = Path("django_apps/asteroid_lab/layers/stack_runner.py").read_text(encoding="utf-8")
    assert "layer_06_commit_validate" in source
    assert "run_layer_06_commit_validate" in source
    assert "floor2_space_link" not in source


def test_layer_06_commit_validate_package_exists() -> None:
    root = Path("django_apps/asteroid_lab/layers")
    assert any(p.name == "layer_06_commit_validate" for p in root.iterdir() if p.is_dir())


def test_remaining_budget_zero_skips_layer_without_call() -> None:
    layer03 = MagicMock()
    runners = (
        _Layer02To05Runner(LAYER_02_EXTERIOR_TRANSPORT, lambda **_k: None),
        _Layer02To05Runner(LAYER_03_RIM_GREEDY_PLACEMENT, layer03),
        _Layer02To05Runner(LAYER_05_INNER_PATTERN_FILL, lambda **_k: None),
        _Layer02To05Runner(LAYER_06_COMMIT_VALIDATE, lambda **_k: None),
    )
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
    )
    assert result.status == StackRunStatus.TIMEOUT_FAIL_CLOSED
    assert result.failed_layer_slug == LAYER_02_EXTERIOR_TRANSPORT
    assert result.completed_layer_slugs == ()
    layer03.assert_not_called()


def test_stack_runner_timeout_records_failed_layer_slug() -> None:
    tick = {"t": 0.0}

    def now_fn() -> float:
        return tick["t"]

    runners = (
        _Layer02To05Runner(LAYER_02_EXTERIOR_TRANSPORT, lambda **_k: tick.update({"t": 100.0})),
        _Layer02To05Runner(LAYER_03_RIM_GREEDY_PLACEMENT, lambda **_k: None),
    )
    cell = DecodedCellDTO(
        x=0,
        y=0,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )
    complete = complete_map_from_overlay_cells(cell)
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=now_fn)
    result = run_layers_02_to_05(complete_map=complete, budget_ctx=ctx, runners=runners)
    assert result.status == StackRunStatus.TIMEOUT_FAIL_CLOSED
    assert result.failed_layer_slug == LAYER_03_RIM_GREEDY_PLACEMENT
    assert LAYER_02_EXTERIOR_TRANSPORT in result.completed_layer_slugs
