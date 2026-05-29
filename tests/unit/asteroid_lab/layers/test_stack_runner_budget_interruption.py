"""Layer 03 budget semantics and stack_runner L2→L3 wiring."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03SkipReason,
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_02_EXTERIOR_TRANSPORT,
    LAYER_03_RIM_MINING_BUNDLES,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
    expand_rim_bundle_candidates,
)
from django_apps.asteroid_lab.layers.stack_runner import _Layer02To05Runner, run_layers_02_to_05
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    expected_golden_rim_anchor_count,
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
    two_seed_catalog,
)


def test_stack_runner_passes_exterior_plan_to_layer_03() -> None:
    captured: dict[str, object] = {}
    plan = minimal_l2_plan_for_golden()

    def fake_l2(**_kwargs: object) -> ExteriorConnectionPlan:
        return plan

    def fake_l3(**kwargs: object) -> None:
        captured.update(kwargs)

    runners = (
        _Layer02To05Runner(LAYER_02_EXTERIOR_TRANSPORT, fake_l2),
        _Layer02To05Runner(LAYER_03_RIM_MINING_BUNDLES, fake_l3),
    )
    complete = golden_5x5_complete_map()
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    run_layers_02_to_05(complete_map=complete, budget_ctx=ctx, runners=runners)
    assert captured.get("exterior_plan") is plan


def test_budget_exhausted_at_anchor_boundary_sets_skip_reason_no_diagnostic() -> None:
    ctx = LayerBudgetContext(
        deadline_monotonic=0.0,
        started_monotonic=0.0,
        now_fn=lambda: 1.0,
    )
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=ctx,
        seed_catalog=two_seed_catalog(),
    )
    assert result.metrics.layer_skip_reason == Layer03SkipReason.BUDGET_EXHAUSTED
    assert result.metrics.budget_skipped_count == 0
    assert result.diagnostic_rejected_candidates == ()
    assert result.metrics.rim_anchor_count == expected_golden_rim_anchor_count()


def test_budget_exhausted_after_projection_appends_skipped_budget_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from django_apps.asteroid_lab.genetic_sample.enums import Direction
    from django_apps.asteroid_lab.layers.contracts.candidates import make_bundle_candidate_for_test
    from django_apps.asteroid_lab.layers.contracts.transport_kind import (
        ResourceKind,
        TransportKind,
    )
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles import expand as expand_mod
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
        ProjectionResult,
    )

    anchor = (6, 4)
    stub = make_bundle_candidate_for_test(
        anchor_coord=anchor,
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        mining_occupied_cells=frozenset({anchor}),
        transport_stub_cells=frozenset({(7, 4), (8, 4)}),
        route_probe_start_coord=(8, 4),
    )

    def fake_project(**_kwargs: object) -> ProjectionResult:
        return ProjectionResult(candidate=stub, reject_reason=None)

    monkeypatch.setattr(expand_mod, "project_miner_seed_at_anchor", fake_project)

    tick = {"n": 0}

    def now_fn() -> float:
        tick["n"] += 1
        return 100.0 if tick["n"] >= 4 else 0.0

    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=now_fn)
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=ctx,
        seed_catalog=two_seed_catalog(),
    )
    assert result.metrics.budget_skipped_count == 1
    assert result.metrics.layer_skip_reason == Layer03SkipReason.BUDGET_EXHAUSTED
    assert len(result.diagnostic_rejected_candidates) == 1
    assert (
        result.diagnostic_rejected_candidates[0].route_probe_status
        is RouteProbeStatus.SKIPPED_BUDGET
    )


def test_missing_exterior_plan_hold() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=None,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
    assert result.metrics.rim_anchor_count > 0
    assert result.metrics.seed_projection_attempt_count == 0
    assert result.metrics.layer_skip_reason == Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN


def test_intrinsic_priority_rank_attempt_order(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles import expand as expand_mod
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
        ProjectionResult,
        project_miner_seed_at_anchor,
    )

    original = project_miner_seed_at_anchor

    def tracking_project(**kwargs: object) -> ProjectionResult:
        seed = kwargs["seed"]
        order.append(seed.pattern_id)  # type: ignore[attr-defined]
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(expand_mod, "project_miner_seed_at_anchor", tracking_project)
    expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )
    first_anchor_patterns = [order[0], order[1]]
    assert first_anchor_patterns == ["m3e_01", "m1e_01"]


def test_stack_runner_passes_l3_result_to_l4_and_overlay_to_l5() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        Layer03ExpansionMetrics,
        build_rim_bundle_candidate_set,
    )
    from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
        LAYER_04_RIM_BUNDLE_PLACEMENT,
        LAYER_05_INNER_PATTERN_FILL,
    )
    from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
        ProvisionalLayoutOverlay,
    )
    from django_apps.asteroid_lab.layers.contracts.rim_placement import (
        build_layer04_rim_placement_result,
    )
    from django_apps.asteroid_lab.layers.stack_runner import _LayerStackRunner, run_layers_02_to_06

    l3_out = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics.empty(),
    )
    overlay = ProvisionalLayoutOverlay.empty()
    l4_out = build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
    )
    captured_l4: dict[str, object] = {}
    captured_l5: dict[str, object] = {}

    def fake_l2(**_kwargs: object) -> ExteriorConnectionPlan:
        return minimal_l2_plan_for_golden()

    def fake_l3(**_kwargs: object) -> object:
        return l3_out

    def fake_l4(**kwargs: object) -> object:
        captured_l4.update(kwargs)
        return l4_out

    def fake_l5(**kwargs: object) -> None:
        captured_l5.update(kwargs)

    runners = (
        _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, fake_l2),
        _LayerStackRunner(LAYER_03_RIM_MINING_BUNDLES, fake_l3),
        _LayerStackRunner(LAYER_04_RIM_BUNDLE_PLACEMENT, fake_l4),
        _LayerStackRunner(LAYER_05_INNER_PATTERN_FILL, fake_l5),
    )
    complete = golden_5x5_complete_map()
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    run_layers_02_to_06(complete_map=complete, budget_ctx=ctx, runners=runners)
    assert captured_l4.get("candidate_set") is l3_out
    assert captured_l5.get("rim_placement_result") is l4_out
    assert captured_l5.get("provisional_overlay") is overlay


def test_stack_runner_layer04_does_not_mutate_complete_map() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import RimBundleCandidateSet
    from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
        LAYER_02_EXTERIOR_TRANSPORT,
        LAYER_03_RIM_MINING_BUNDLES,
        LAYER_04_RIM_BUNDLE_PLACEMENT,
    )
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from django_apps.asteroid_lab.layers.stack_runner import _LayerStackRunner, run_layers_02_to_06

    complete = golden_5x5_complete_map()
    cells_before = complete.cells

    def fake_l2(**_kwargs: object) -> ExteriorConnectionPlan:
        return minimal_l2_plan_for_golden()

    def fake_l3(**kwargs: object) -> RimBundleCandidateSet:
        from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.run import (
            run_layer_03_rim_mining_bundles,
        )

        return run_layer_03_rim_mining_bundles(
            complete_map=kwargs["complete_map"],
            exterior_plan=kwargs["exterior_plan"],
            budget_ctx=kwargs["budget_ctx"],
            seed_catalog=two_seed_catalog(),
        )

    runners = (
        _LayerStackRunner(LAYER_02_EXTERIOR_TRANSPORT, fake_l2),
        _LayerStackRunner(LAYER_03_RIM_MINING_BUNDLES, fake_l3),
        _LayerStackRunner(LAYER_04_RIM_BUNDLE_PLACEMENT, run_layer_04_rim_bundle_placement),
    )
    ctx = LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0)
    run_layers_02_to_06(complete_map=complete, budget_ctx=ctx, runners=runners)
    assert complete.cells == cells_before
